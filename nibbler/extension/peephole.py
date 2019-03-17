from ctypes import py_object
from ctypes import pythonapi
from types import CodeType

from ..containers import Context

_PyCode_Optimize = pythonapi.PyCode_Optimize
_PyCode_Optimize.restype = py_object

__all__ = ["EXTENSION"]


def peephole(code: CodeType, context: Context) -> CodeType:
    co_consts = list(code.co_consts)
    co_code = _PyCode_Optimize(
        py_object(code.co_code),
        py_object(co_consts),
        py_object(code.co_names),
        py_object(code.co_lnotab),
    )
    return CodeType(
        code.co_argcount,
        code.co_kwonlyargcount,
        code.co_nlocals,
        code.co_stacksize,
        code.co_flags,
        co_code,
        tuple(co_consts),
        code.co_names,
        code.co_varnames,
        code.co_filename,
        code.co_name,
        code.co_firstlineno,
        code.co_lnotab,
        code.co_freevars,
        code.co_cellvars,
    )


EXTENSION = peephole
