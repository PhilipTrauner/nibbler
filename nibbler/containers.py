from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Callable
from typing import Dict

__all__ = ["Context"]


@dataclass
class Context:
    module_namespace: Dict[str, Any]
    constants: Dict[str, Any] = field(default_factory=dict)
    inline_functions: Dict[str, Callable] = field(default_factory=dict)
    debug: bool = False
