from types import CodeType

from ..constants import ARG
from ..constants import EXTENDED_ARG
from ..constants import LOAD_FAST
from ..constants import LOAD_GLOBAL
from ..constants import OP
from ..constants import STEP
from ..containers import Context
from ..util import Offset
from ..util import pack_op
from ..util import unpack_op

__all__ = ["EXTENSION"]


def global_to_fast(code: CodeType, context: Context) -> CodeType:
    ops = []

    offset = Offset()
    pos = 0
    while pos < len(code.co_code):
        op, unpacked_op = unpack_op(code.co_code, pos)

        if (
            unpacked_op[OP] == LOAD_GLOBAL
            and code.co_names[unpacked_op[ARG]] in code.co_varnames
        ):
            ops += offset.swap(
                pos,
                unpacked_op,
                pack_op(
                    LOAD_FAST, code.co_varnames.index(code.co_names[unpacked_op[ARG]])
                ),
            )
        elif unpacked_op[OP] != EXTENDED_ARG:
            ops += pack_op(unpacked_op[OP], unpacked_op[ARG])

        pos += STEP

    return CodeType(
        code.co_argcount,
        code.co_kwonlyargcount,
        code.co_nlocals,
        code.co_stacksize,
        code.co_flags,
        b"".join(ops),
        code.co_consts,
        code.co_names,
        code.co_varnames,
        "<string>",
        code.co_name,
        1,
        b"",
        code.co_freevars,
        code.co_cellvars,
    )


EXTENSION = global_to_fast
