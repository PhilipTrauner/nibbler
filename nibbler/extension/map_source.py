from io import StringIO as StringIo
from tempfile import NamedTemporaryFile
from types import CodeType

from black import format_str
from uncompyle6.main import decompile

from ..containers import Context

__all__ = ["EXTENSION"]

INDENTATION_SIZE = 4
LINE_LENGTH = 80


def map_source(code: CodeType, context: Context) -> CodeType:
    # Trick uncompyle6 into generating parse-able code
    # for impossible constructs (e.g. constant funtions)
    class CallableMock:
        def __init__(self, name: str):
            self.name = name

        def __repr__(self):
            return self.name

    wrapped_const_code = CodeType(
        code.co_argcount,
        code.co_kwonlyargcount,
        code.co_nlocals,
        code.co_stacksize,
        code.co_flags,
        code.co_code,
        tuple(
            (
                CallableMock(
                    const.__name__
                    if not const.__name__.startswith("<")
                    else f"anonymous_func_{abs(hash(const))}"
                )
                if callable(const)
                else const
                for const in code.co_consts
            )
        ),
        code.co_names,
        code.co_varnames,
        code.co_filename,
        code.co_name,
        code.co_firstlineno,
        code.co_lnotab,
        code.co_freevars,
        code.co_cellvars,
    )

    fn_name = (
        code.co_name
        if not code.co_name.startswith("<")
        else f"anonymous_func_{abs(hash(code))}"
    )
    tmp_file = NamedTemporaryFile(prefix=f"{fn_name}__", suffix="__.py", delete=False)

    raw_buf = StringIo()
    decompile(None, wrapped_const_code, out=raw_buf)
    raw_buf.flush()

    buf = []
    # There doesn't appear to be an easy way to silence startup prints.
    # Luckily, the are all prefixed with a '# '.
    other_than_pound = False
    for line in raw_buf.getvalue().split("\n"):
        if not line.startswith("# "):
            other_than_pound = True
        if other_than_pound:
            # Indent by one level
            buf.append(f"{' ' * INDENTATION_SIZE}{line}")

    # Define a dummy function
    fn_code = "\n".join(buf)
    # To-Do: Use real function signature
    wrapped_fn_code = format_str(f"def {fn_name}():\n{fn_code}", LINE_LENGTH)

    tmp_file.write(wrapped_fn_code.encode())

    # Compile code to obtain line-to-op mapping (co_lnotab)
    tmp_code = compile(wrapped_fn_code, tmp_file.name, "exec").co_consts[0]

    return CodeType(
        code.co_argcount,
        code.co_kwonlyargcount,
        code.co_nlocals,
        code.co_stacksize,
        code.co_flags,
        code.co_code,
        code.co_consts,
        code.co_names,
        code.co_varnames,
        tmp_file.name,
        code.co_name,
        1,
        tmp_code.co_lnotab,
        code.co_freevars,
        code.co_cellvars,
    )


EXTENSION = map_source
