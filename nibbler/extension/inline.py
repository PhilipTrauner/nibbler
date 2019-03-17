from types import CodeType
from typing import Any
from typing import Dict
from typing import List

from ..constants import ARG
from ..constants import CALL_FUNCTION
from ..constants import EXTENDED_ARG
from ..constants import LOAD_CONST
from ..constants import LOAD_FAST
from ..constants import LOAD_GLOBAL
from ..constants import OP
from ..constants import STEP
from ..constants import STORE_FAST
from ..containers import Context
from ..util import needs_extended
from ..util import Offset
from ..util import pack_op
from ..util import pos_excluding_last_return
from ..util import previous_op
from ..util import unpack_op


__all__ = ["EXTENSION"]


def rewrite_inlined(
    code: CodeType,
    consts: Dict[str, Any],
    names: Dict[str, str],
    varnames: Dict[str, str],
) -> List[bytes]:
    consts_index = len(consts)
    names_index = len(names)
    varsnames_index = len(varnames)

    offset = Offset()
    ops = []

    pos = 0
    while pos < pos_excluding_last_return(code.co_code):
        # Fetch and decode operand
        op, unpacked_op = unpack_op(code.co_code, pos)

        # Remap load indices
        if unpacked_op[OP] == LOAD_CONST:
            const = code.co_consts[unpacked_op[ARG]]
            if const in consts:
                index = consts.index(const)
            else:
                consts.append(code.co_consts[unpacked_op[ARG]])
                index = consts_index
                consts_index += 1

            ops += offset.swap(pos, unpacked_op, pack_op(LOAD_CONST, index))

        elif unpacked_op[OP] == STORE_FAST:
            varname = code.co_varnames[unpacked_op[ARG]]
            if varname in varnames:
                index = varnames.index(varname)
            else:
                varnames.append(code.co_varnames[unpacked_op[ARG]])
                index = varsnames_index
                varsnames_index += 1

            ops += offset.swap(pos, unpacked_op, pack_op(STORE_FAST, index))

        elif unpacked_op[OP] == LOAD_GLOBAL:
            name = code.co_names[unpacked_op[ARG]]
            if name in names:
                index = names.index(name)
            else:
                names.append(code.co_names[unpacked_op[ARG]])
                index = names_index
                names_index += 1

            ops += offset.swap(pos, unpacked_op, pack_op(LOAD_GLOBAL, index))

        elif unpacked_op[OP] == LOAD_FAST:
            varname = code.co_varnames[unpacked_op[ARG]]
            if varname in varnames:
                index = varnames.index(varname)
            else:
                varnames.append(varname)
                index = varsnames_index
                varsnames_index += 1

            ops += offset.swap(pos, unpacked_op, pack_op(LOAD_FAST, index))

        elif unpacked_op[OP] != EXTENDED_ARG:
            ops += pack_op(*unpacked_op)

        pos += STEP

    return offset.fix_abs_jumps(b"".join(ops))


def inline(code: CodeType, context: Context) -> CodeType:
    consts = list(code.co_consts)
    names = list(code.co_names)
    varnames = list(code.co_varnames)

    ops = []

    offset = Offset()
    pos = 0
    while pos < len(code.co_code):
        op, unpacked_op = unpack_op(code.co_code, pos)

        # Parameter-less call to inlined function
        if unpacked_op[OP] == CALL_FUNCTION and unpacked_op[ARG] == 0:
            # Fetch previous op (ignoring own EXTENDED_ARG)
            prev_pos, unpacked_prev_op = previous_op(pos, code.co_code)
            prev_pos = (
                prev_pos - STEP if needs_extended(unpacked_prev_op[ARG]) else prev_pos
            )

            if (
                unpacked_prev_op[OP] == LOAD_GLOBAL
                and code.co_names[unpacked_prev_op[ARG]] in context.inline_functions
            ):
                # Remove all preceding instructions pertaining to the CALL_FUNCTION
                ops = ops[: -(pos - prev_pos) // STEP]

                # LOAD_, CALL_, POP_TOP
                offset.strip(prev_pos, pos + (STEP * 2))

                inline_offset = Offset(prev_pos)

                inlined_co_code = inline_offset.fix_abs_jumps(
                    rewrite_inlined(
                        context.inline_functions[
                            code.co_names[unpacked_prev_op[ARG]]
                        ].__code__,
                        consts,
                        names,
                        varnames,
                    )
                )

                inlined_ops = [
                    inlined_co_code[idx : idx + STEP]
                    for idx in range(0, len(inlined_co_code) * STEP, STEP)
                ]

                offset.add(pos, len(inlined_ops) // 2)

                ops += inlined_ops

                # Skip POP_TOP
                pos += STEP * 2

                continue

            else:
                ops += pack_op(*unpacked_op)
        elif unpacked_op[OP] != EXTENDED_ARG:
            ops += pack_op(*unpacked_op)

        pos += STEP

    return CodeType(
        code.co_argcount,
        code.co_kwonlyargcount,
        len(varnames),
        code.co_stacksize,
        code.co_flags,
        offset.fix_abs_jumps(b"".join(ops)),
        tuple(consts),
        tuple(names),
        tuple(varnames),
        "<string>",
        code.co_name,
        1,
        b"",
        code.co_freevars,
        code.co_cellvars,
    )


EXTENSION = inline
