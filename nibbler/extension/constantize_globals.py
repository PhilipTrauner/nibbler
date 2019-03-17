from types import CodeType

from ..constants import ARG
from ..constants import EXTENDED_ARG
from ..constants import LOAD_CONST
from ..constants import LOAD_GLOBAL
from ..constants import OP
from ..constants import STEP
from ..containers import Context
from ..util import Offset
from ..util import pack_op
from ..util import unpack_op

__all__ = ["EXTENSION"]


def constantize_globals(code: CodeType, context: Context) -> CodeType:
    consts = list(code.co_consts)
    const_map = {}

    ops = []

    offset = Offset()
    pos = 0
    while pos < len(code.co_code):
        op, unpacked_op = unpack_op(code.co_code, pos)

        if unpacked_op[OP] == LOAD_GLOBAL:
            name = code.co_names[unpacked_op[ARG]]
            if name in context.constants:
                if name not in const_map:
                    value = context.constants[name]
                    consts.append(value)
                    const_map[name] = len(consts) - 1

                ops += offset.swap(
                    pos, unpacked_op, pack_op(LOAD_CONST, const_map[name])
                )
            else:
                ops += pack_op(unpacked_op[OP], unpacked_op[ARG])
        elif unpacked_op[OP] != EXTENDED_ARG:
            ops += pack_op(unpacked_op[OP], unpacked_op[ARG])

        pos += STEP

    return CodeType(
        code.co_argcount,
        code.co_kwonlyargcount,
        code.co_nlocals,
        code.co_stacksize,
        code.co_flags,
        offset.fix_abs_jumps(b"".join(ops)),
        tuple(consts),
        code.co_names,
        code.co_varnames,
        "<string>",
        code.co_name,
        1,
        b"",
        code.co_freevars,
        code.co_cellvars,
    )


EXTENSION = constantize_globals
