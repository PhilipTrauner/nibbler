<p align="center">
<img src="https://user-images.githubusercontent.com/9287847/52054870-21754d80-255e-11e9-9169-843316357763.png" width="600px" alt="nibbler"/>
</p>

---
[![Python 3.7](https://img.shields.io/badge/python-3.7-%233572A5.svg)](https://docs.python.org/3/whatsnew/3.7.html)
[![PyPI version](https://badge.fury.io/py/nibbler.svg)](https://badge.fury.io/py/nibbler)
[![Not production ready](https://img.shields.io/badge/production%20ready-hell%20no-red.svg)]()
[![Travis status](https://travis-ci.org/PhilipTrauner/nibbler.svg?branch=master)](https://travis-ci.org/PhilipTrauner/nibbler)

**nibbler** is a runtime bytecode optimizer.

It explores the concept of using existing Python syntax features such as *type annotations* and *decorators* to **speed up** code execution by running additional bytecode optimization passes that make use of runtime context provided through these means.

## Optimization passes
* [`inline`](https://github.com/PhilipTrauner/nibbler/blob/master/nibbler/extension/inline.py)  
	Inlines parameter-less calls to functions that are decorated with `@nibbler.inline`.
* [`constantize_globals`](https://github.com/PhilipTrauner/nibbler/blob/master/nibbler/extension/constantize_globals.py)  
	Copies the value of globals that were marked constant (with a `Constant` type annotation or with the `@nibbler.constant` decorator) into the `co_consts` tuple of functions that would normally have to access the global namespace, which speeds up variable access. This also applies to builtins (`any`, `all`, `print`, ...).
* [`precompute_conditionals`](https://github.com/PhilipTrauner/nibbler/blob/master/nibbler/extension/precompute_conditionals.py)  
	Strips out conditionals that test constants which the peephole optimizer doesn't pick up on.
* [`global_to_fast`](https://github.com/PhilipTrauner/nibbler/blob/master/nibbler/extension/global_to_fast.py)  
	Transforms global variable loads to local variable loads if a local variable with the same name exists (mostly a cleanup pass for [`inline`](https://github.com/PhilipTrauner/nibbler/blob/master/nibbler/extension/inline.py))
* [`peephole`](https://github.com/PhilipTrauner/nibbler/blob/master/nibbler/extension/peephole.py)  
	Invokes the [Python peephole optimizer](https://github.com/python/cpython/blob/master/Python/peephole.c) with additional context.


## Usage
```python
from typing import Iterable

from nibbler import Constant, Nibbler

DEBUG: Constant[bool] = False

nibbler = Nibbler(globals())


@nibbler.inline
def square(number: int, base: int) -> int:
    result = number ** base
    return result


@nibbler.nibble
def sequential_square(numbers: Iterable[int]) -> int:
    product = 0
    base = 2
    for number in numbers:
        square()

        if DEBUG:
            print(result)

        product += result

    print(f"Result: {product}")

    return product


sequential_square(range(4))
```
<p align="center"><b>↓</b></p>

```
Result: 14
```

Examining the function bytecode reveals which optimizations **nibbler** has performed:
```
  2           0 LOAD_CONST               1 (0)
              2 STORE_FAST               1 (product)

  3           4 LOAD_CONST               2 (2)
              6 STORE_FAST               2 (base)

  4           8 SETUP_LOOP              28 (to 38)
             10 LOAD_FAST                0 (numbers)
             12 GET_ITER
        >>   14 FOR_ITER                20 (to 36)
             16 STORE_FAST               3 (number)

  5          18 LOAD_FAST                3 (number)
             20 LOAD_FAST                2 (base)
             22 BINARY_POWER
             24 STORE_FAST               4 (result)

  6          26 LOAD_FAST                1 (product)
             28 LOAD_FAST                4 (result)
             30 INPLACE_ADD
             32 STORE_FAST               1 (product)
             34 JUMP_ABSOLUTE           14
        >>   36 POP_BLOCK

  8     >>   38 LOAD_CONST               5 (<built-in function print>)
             40 LOAD_CONST               3 ('Result: ')
             42 LOAD_FAST                1 (product)
             44 FORMAT_VALUE             0
             46 BUILD_STRING             2
             48 CALL_FUNCTION            1
             50 POP_TOP

  9          52 LOAD_FAST                1 (product)
             54 RETURN_VALUE
```

* The `square` function was inlined ([`inline`](https://github.com/PhilipTrauner/nibbler/blob/master/nibbler/extension/inline.py)) (18-24)
* Conditional (`if DEBUG`) was stripped out, because `DEBUG` was declared a constant ([`precompute_conditionals`](https://github.com/PhilipTrauner/nibbler/blob/master/nibbler/extension/precompute_conditionals.py)) (26)
* The `print` function was promoted to a function-level constant ([`constantize_globals`](https://github.com/PhilipTrauner/nibbler/blob/master/nibbler/extension/constantize_globals.py)) (38)

## Installation
```sh
pip3 install nibbler
```

## FAQ

* Is this production ready?  
	Hell no.
* Why is it called **nibbler**?  
	¯\\\_(ツ)\_/¯

## Prior Art
* [fatoptimizer](https://github.com/vstinner/fatoptimizer)
* [PEP 510](https://www.python.org/dev/peps/pep-0510/)
* [PEP 511](https://www.python.org/dev/peps/pep-0511/)
* [falcon](https://github.com/rjpower/falcon)
