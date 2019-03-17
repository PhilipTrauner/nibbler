import builtins

from nibbler import Constant
from nibbler import Nibbler
from nibbler.containers import Context

FOO: Constant[str] = "bar"

nibbler = Nibbler(globals(), debug=True)


@nibbler.constant
def constant():
    pass


@nibbler.inline
def inline():
    pass


def test_context() -> None:
    assert (
        Context(
            globals(),
            {
                "FOO": "bar",
                "constant": constant,
                **{
                    name: func
                    for name, func in (
                        (name, getattr(builtins, name))
                        for name in dir(builtins)
                        if not name.startswith("_") and name[0].lower() == name[0]
                    )
                    if callable(func)
                },
            },
            {"inline": inline},
            True,
        )
        == nibbler.context
    )
