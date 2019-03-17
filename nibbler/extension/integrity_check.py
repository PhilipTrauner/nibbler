import builtins
from types import CodeType

from ..constants import ARG
from ..constants import LOAD_CONST
from ..constants import LOAD_DEREF
from ..constants import LOAD_FAST
from ..constants import LOAD_GLOBAL
from ..constants import OP
from ..constants import REVERSE_OPMAP
from ..constants import STEP
from ..containers import Context
from ..util import unpack_op

__all__ = ["EXTENSION"]


def integrity_check(code: CodeType, context: Context) -> CodeType:
    CHECKED_INSTRUCTIONS = {
        LOAD_GLOBAL: (
            lambda index: index <= len(code.co_names)
            and code.co_names[index] in context.module_namespace
            or getattr(builtins, code.co_names[index], None) is not None,
            lambda index: "out of bounds access"
            if index > len(code.co_names)
            else f"'{code.co_names[index]}' is not defined",
        ),
        # Constants do not have names, but we can still validate out of bounds access
        LOAD_CONST: (lambda index: index <= len(code.co_consts), None),
        # Local variables can only be accessed at runtime
        LOAD_FAST: (lambda index: index <= code.co_nlocals, None),
        # Cells are bound to the function type, not the code
        LOAD_DEREF: (lambda index: index <= len(code.co_freevars), None),
    }

    pos = 0
    while pos < len(code.co_code):
        op, unpacked_op = unpack_op(code.co_code, pos)

        if unpacked_op[OP] in CHECKED_INSTRUCTIONS:
            if not CHECKED_INSTRUCTIONS[unpacked_op[OP]][0](unpacked_op[ARG]):
                error = (
                    CHECKED_INSTRUCTIONS[unpacked_op[OP]][1](unpacked_op[ARG])
                    if callable(CHECKED_INSTRUCTIONS[unpacked_op[OP]][1])
                    else None
                )
                raise ValueError(
                    f"invalid {REVERSE_OPMAP[unpacked_op[OP]]} argument"
                    f"{f' ({error})'}"
                    if error is not None
                    else ""
                )

        pos += STEP

    return code


EXTENSION = integrity_check
