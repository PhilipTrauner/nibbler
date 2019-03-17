from dis import dis
from types import CodeType

from ..containers import Context


def debug(code: CodeType, context: Context) -> CodeType:
    dis(code)

    return code


EXTENSION = debug
