from nibbler import Nibbler
from nibbler.extension.map_source import EXTENSION as map_source

CODE = """def foo():
    a = 10
    b = 20
    c = 30
    print("bar")
"""

nibbler = Nibbler(globals(), config=[map_source])

nibbler._constant_variables["print"] = print


@nibbler.nibble
def foo():
    a = 10  # noqa: F841
    b = 20  # noqa: F841
    c = 30  # noqa: F841
    print("bar")


def test_map_source() -> None:
    assert open(foo.__code__.co_filename, "r").read() == CODE
