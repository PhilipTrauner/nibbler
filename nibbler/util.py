from opcode import hasjabs
from opcode import hasjrel
from struct import pack
from struct import unpack
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from .constants import ARG
from .constants import EXTENDED_ARG
from .constants import INSTRUCTION_FORMAT
from .constants import LOAD_INSTRUCTIONS
from .constants import OP
from .constants import STEP


def unpack_op(co_code: bytes, pos: int) -> Tuple[int, int]:
    co_code_len = len(co_code)
    if pos % 2 or pos < 0 or pos >= co_code_len:
        raise ValueError(f"invalid pos value 0 <= pos < {co_code_len} ({pos})")
    op = co_code[pos : pos + STEP]
    unpacked_op = unpack(INSTRUCTION_FORMAT, op)
    extended_arg = 0
    # Preceding / succeeding (if reverse) op might be an EXTENDED_ARG
    if pos >= 2:
        previous_op = unpack(INSTRUCTION_FORMAT, co_code[pos - STEP : pos])
        if previous_op[0] == EXTENDED_ARG:
            extended_arg = previous_op[ARG]
    return (op, (unpacked_op[OP], (extended_arg << 8) + unpacked_op[ARG]))


def needs_extended(arg: int) -> bool:
    return arg > 255  # 0b11111111


def pack_op(op: int, arg: int) -> List[bytes]:
    min_val = 0
    max_val = 65536
    if arg < min_val or arg >= max_val:
        raise ValueError(f"invalid arg value ({arg}) ({min_val} <= arg < {max_val})")
    ops = []
    if needs_extended(arg):
        extended_arg = arg >> 8
        ops.append(pack(INSTRUCTION_FORMAT, EXTENDED_ARG, extended_arg))
    ops.append(pack(INSTRUCTION_FORMAT, op, arg & 255))  # 0b11111111
    return ops


class Offset:
    def __init__(self, offset: int = 0):
        self._offsets: Dict[int, int] = {0: offset}

    def strip(self, from_: int, to: int) -> None:
        is_extended = needs_extended(to)

        start_pos = from_ - STEP if is_extended else from_
        offset = -(to - start_pos)
        self._offsets[start_pos + self.offset(start_pos)] = offset

    def add(self, pos: int, op_count: int) -> None:
        self._offsets[pos + self.offset(pos)] = op_count * STEP

    def swap(
        self, pos: int, unpacked_op: Tuple[int, int], new_op: List[bytes]
    ) -> List[bytes]:
        is_extended = needs_extended(unpacked_op[ARG])

        offset = None
        if len(new_op) == 2 and not is_extended:
            offset = STEP
        elif len(new_op) == 1 and is_extended:
            offset = -STEP

        if offset is not None:
            self._offsets[pos] = offset

        return new_op

    def offset(self, pos: int) -> int:
        return sum((self._offsets[pos_] for pos_ in self._offsets if pos_ <= pos))

    def rel_offset(self, pos: int, arg: int) -> int:
        return sum(
            (
                self._offsets[pos_]
                for pos_ in self._offsets
                if pos_ >= pos and pos_ <= pos + arg
            )
        )

    def fix_abs_jumps(self, co_code: bytes) -> bytes:
        ops: List[bytes] = []

        pos = 0
        while pos < len(co_code):
            op, unpacked_op = unpack_op(co_code, pos)

            if unpacked_op[OP] in hasjabs:
                old_is_extended = needs_extended(unpacked_op[ARG])
                new_is_extended = needs_extended(
                    unpacked_op[ARG]
                    + self.offset(
                        unpacked_op[ARG] - STEP if unpacked_op[ARG] < pos else pos
                    )
                )

                offset = None
                if not old_is_extended and new_is_extended:
                    offset = STEP
                elif old_is_extended and not new_is_extended:
                    offset = -STEP

                if offset is not None:
                    self._offsets[pos] = offset

                ops += pack_op(
                    unpacked_op[OP],
                    unpacked_op[ARG]
                    + self.offset(
                        unpacked_op[ARG] - STEP if unpacked_op[ARG] < pos else pos
                    ),
                )
            elif unpacked_op[OP] in hasjrel:
                old_is_extended = needs_extended(unpacked_op[ARG])
                new_is_extended = needs_extended(
                    unpacked_op[ARG] + self.rel_offset(pos, unpacked_op[ARG])
                )

                offset = None
                if not old_is_extended and new_is_extended:
                    offset = STEP
                elif old_is_extended and not new_is_extended:
                    offset = -STEP

                if offset is not None:
                    self._offsets[pos] = offset

                ops += pack_op(
                    unpacked_op[OP],
                    unpacked_op[ARG] + self.rel_offset(pos, unpacked_op[ARG]),
                )
            elif unpacked_op[OP] != EXTENDED_ARG:
                ops += pack_op(*unpacked_op)

            pos += STEP

        return b"".join(ops)


def previous_op(pos: int, co_code: bytes) -> Optional[bytes]:
    pos -= STEP

    while pos >= 0:
        op, unpacked_op = unpack_op(co_code, pos)

        if unpacked_op[OP] != EXTENDED_ARG:
            return pos, unpacked_op

        pos -= STEP

    return None


def pos_excluding_last_return(co_code: bytes) -> Optional[int]:
    # Start from the bottom and exclude return (be it implicit or explicit)
    pos = len(co_code) - STEP * 2

    while pos >= 0:
        # Fetch and decode operand
        op, unpacked_op = unpack_op(co_code, pos)

        # Stop trimming LOAD_* instructions as soon as a non LOAD_* instruction
        # is encountered
        if unpacked_op[OP] not in LOAD_INSTRUCTIONS:
            return (pos + STEP) if not needs_extended(unpacked_op[ARG]) else pos

        pos -= STEP
