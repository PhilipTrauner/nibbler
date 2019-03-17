from nibbler import Nibbler

nibbler = Nibbler(globals())


@nibbler.inline
def bar(b: int, c: int) -> int:
    a = b + c
    return a


def test_inline() -> None:
    def foo_1() -> int:
        b = 10
        c = 20
        a = b + c
        return a

    @nibbler.nibble
    def foo_2() -> int:
        b = 10  # noqa: F841
        c = 20  # noqa: F841
        bar()
        return a  # noqa: F821

    assert foo_1() == foo_2()
    assert foo_1.__code__.co_code == foo_2.__code__.co_code
