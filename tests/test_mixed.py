from typing import List

from nibbler import Constant
from nibbler import Nibbler

DEBUG: Constant[bool] = False

nibbler = Nibbler(globals())


@nibbler.inline
def square(result: int, number: int, base: int) -> int:
    result = number ** base  # noqa: F841


@nibbler.nibble
def sequential_square(numbers: List[int]) -> int:
    product = 0
    base = 2  # noqa: F841
    for number in numbers:
        square()
        product += result  # noqa: F821

    if DEBUG:
        print(f"Result: {product}")

    return product


def test_mixed() -> None:
    assert sequential_square((1, 2, 3)) == 14
