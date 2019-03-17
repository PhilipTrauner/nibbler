from __future__ import annotations

import builtins
from copy import deepcopy
from enum import Enum
from sys import modules
from types import FunctionType
from typing import _eval_type
from typing import Any
from typing import Callable
from typing import Dict
from typing import List

from .annotations import Constant
from .config import DEFAULT_CONFIG
from .constants import CODE_TYPE
from .containers import Context

CONSTANT_TYPE = type(Constant)
MODULE_TYPE = type(modules[list(modules.keys())[0]])


__all__ = ["Constant", "Nibbler"]


class FunctionKind(Enum):
    CONSTANT = 1
    INLINE = 2


class Nibbler:
    def __init__(
        self,
        module_namespace: Dict[str, Any],
        deep_copy: bool = True,
        config: List[Callable[CODE_TYPE, Context]] = DEFAULT_CONFIG,
        debug: bool = False,
    ):
        if "__name__" not in module_namespace:
            # To-Do: Subclass ValueError
            raise ValueError("provided namespace is not a module")

        self._module_namespace: Dict[str, Any] = module_namespace
        self._config: List[Callable[CODE_TYPE, Context]] = config
        self._debug: bool = debug

        self._module_name: str = module_namespace["__name__"]
        self._module: MODULE_TYPE = modules[self._module_name]
        self._evaluated_annotations: Dict[str, Any] = {
            name: _eval_type(annotation, module_namespace, {})
            for name, annotation in (
                module_namespace["__annotations__"]
                if "__annotations__" in module_namespace
                else {}
            ).items()
        }

        self._constant_variables: Dict[str, Any] = {
            name: deepcopy(value) if deep_copy else value
            for name, value in module_namespace.items()
            if name in self._evaluated_annotations
            # Marked Constant or Constant[SubType]
            and (
                type(self._evaluated_annotations[name]) is CONSTANT_TYPE
                or (
                    hasattr(self._evaluated_annotations[name], "__origin__")
                    and type(self._evaluated_annotations[name].__origin__)
                    is CONSTANT_TYPE
                )
            )
        }
        # Mark builtins as constant functions
        self._constant_functions: Dict[str, Callable] = {
            name: func
            for name, func in (
                (name, getattr(builtins, name))
                for name in dir(builtins)
                if not name.startswith("_") and name[0].lower() == name[0]
            )
            if callable(func)
        }
        self._inline_functions: Dict[str, Callable] = {}

        self._function_mapping: Dict[FunctionKind, Dict[str, Callable]] = {
            FunctionKind.CONSTANT: self._constant_functions,
            FunctionKind.INLINE: self._inline_functions,
        }

    @property
    def context(self) -> Context:
        return Context(
            self._module_namespace,
            {**self._constant_variables, **self._constant_functions},
            self._inline_functions,
            self._debug,
        )

    def _ensure_matching_module(self, callable_: Callable):
        if callable_.__module__ != self._module_name:
            raise ValueError(
                f"function not part of provided module '{self._module_name}'"
            )

    def _decorator(self, callable_: Callable, function_type: FunctionKind) -> Callable:
        if not hasattr(callable_, "__name__"):
            # To-Do: Subclass ValueError
            raise ValueError(f"anonymous functions not yet supported")

        self._ensure_matching_module(callable_)

        try:
            function_type_dict = self._function_mapping[function_type]
        except KeyError:
            # To-Do: Subclass ValueError
            raise ValueError(f"unsupported function type ('{function_type}')")

        for function_type_ in self._function_mapping:
            if callable_ in self._function_mapping[function_type_].values():
                # To-Do: Subclass ValueError
                raise ValueError(f"function already marked as '{function_type.name}'")

        function_type_dict[callable_.__name__] = callable_

        return callable_

    def constant(self, callable_: Callable) -> Callable:
        return self._decorator(callable_, FunctionKind.CONSTANT)

    def inline(self, callable_: Callable) -> Callable:
        return self._decorator(callable_, FunctionKind.INLINE)

    def nibble(self, callable_: Callable) -> Callable:
        self._ensure_matching_module(callable_)

        context = self.context

        code = callable_.__code__

        for extension in self._config:
            code = extension(code, context)

        return FunctionType(code, callable_.__globals__, code.co_name)
