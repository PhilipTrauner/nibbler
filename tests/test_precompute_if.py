from nibbler import Nibbler
from nibbler.extension.precompute_conditionals import (
    EXTENSION as precompute_conditionals,
)


def square(number: int, base: int) -> int:
    DEBUG()  # noqa: F821
    result = number ** base
    if DEBUG:  # noqa: F821
        print(f"Result: {result}")
    return result


def square_stripped_conditional(number: int, base: int) -> int:
    DEBUG()  # noqa: F821
    result = number ** base
    print(f"Result: {result}")
    return result


def square_stripped_block(number: int, base: int) -> int:
    DEBUG()  # noqa: F821
    result = number ** base
    return result


def test_precompute_if() -> None:
    nibbler = Nibbler(globals(), config=[precompute_conditionals])

    nibbler._constant_variables["DEBUG"] = True

    assert (
        nibbler.nibble(square).__code__.co_code
        == square_stripped_conditional.__code__.co_code
    )

    nibbler._constant_variables["DEBUG"] = False

    assert (
        nibbler.nibble(square).__code__.co_code
        == square_stripped_block.__code__.co_code
    )
