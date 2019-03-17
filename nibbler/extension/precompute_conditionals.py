from types import CodeType

from ..constants import ARG
from ..constants import EXTENDED_ARG
from ..constants import LOAD_CONST
from ..constants import LOAD_GLOBAL
from ..constants import OP
from ..constants import POP_JUMP_IF_FALSE
from ..constants import POP_JUMP_IF_TRUE
from ..constants import STEP
from ..containers import Context
from ..util import needs_extended
from ..util import Offset
from ..util import pack_op
from ..util import previous_op
from ..util import unpack_op

__all__ = ["EXTENSION"]


def precompute_conditionals(code: CodeType, context: Context) -> CodeType:
    ops = []

    offset = Offset()
    pos = 0
    while pos < len(code.co_code):
        op, unpacked_op = unpack_op(code.co_code, pos)

        if unpacked_op[OP] in (POP_JUMP_IF_FALSE, POP_JUMP_IF_TRUE):
            # Fetch previous op (ignoring own EXTENDED_ARG)
            prev_pos, unpacked_prev_op = previous_op(pos, code.co_code)
            prev_pos = (
                prev_pos - STEP if needs_extended(unpacked_prev_op[ARG]) else prev_pos
            )

            # Only apply conditional precomputing for globals that were marked constant or
            # constants (which the peephole optimizer ignored)
            if (
                (
                    unpacked_prev_op[OP] == LOAD_GLOBAL
                    and code.co_names[unpacked_prev_op[ARG]] in context.constants
                )
                or unpacked_prev_op[OP] == LOAD_CONST
                # To-Do: Support "negative" jumps
                and unpacked_op[ARG] > pos
            ):
                value = (
                    context.constants[code.co_names[unpacked_prev_op[ARG]]]
                    if unpacked_prev_op[OP] == LOAD_GLOBAL
                    else code.co_consts[unpacked_prev_op[ARG]]
                )
                # Reuse same logic for IF_TRUE and IF_FALSE
                if unpacked_op[OP] == POP_JUMP_IF_FALSE:
                    value = not value

                # Remove all preceding instructions pertaining to the CALL_FUNCTION
                ops = ops[: -(pos - prev_pos) // STEP]

                # Skip entire block
                if value:
                    offset.strip(prev_pos, unpacked_op[ARG])

                    pos = unpacked_op[ARG]

                    continue
                # Skip jump instruction
                else:
                    offset.strip(prev_pos, pos + STEP)

            else:
                ops += pack_op(*unpacked_op)
        elif unpacked_op[OP] != EXTENDED_ARG:
            ops += pack_op(*unpacked_op)

        pos += STEP

    return CodeType(
        code.co_argcount,
        code.co_kwonlyargcount,
        code.co_nlocals,
        code.co_stacksize,
        code.co_flags,
        offset.fix_abs_jumps(b"".join(ops)),
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


EXTENSION = precompute_conditionals
