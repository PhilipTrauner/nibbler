from typing import _Final
from typing import _GenericAlias
from typing import _Immutable
from typing import _SpecialForm
from typing import _tp_cache
from typing import _type_check

__all__ = ["Constant"]


class SubscriptableAlias(_Final, _Immutable, _root=True):
    __slots__ = ("_name", "_doc")

    def __new__(cls, *args, **kwds):
        return super().__new__(cls)

    def __init__(self, name, doc):
        self._name = name
        self._doc = doc

    def __eq__(self, other):
        if not isinstance(other, _SpecialForm):
            return NotImplemented
        return self._name == other._name

    def __hash__(self):
        return hash((self._name,))

    def __repr__(self):
        return "nibbler." + self._name

    def __reduce__(self):
        return self._name

    def __call__(self, *args, **kwds):
        raise TypeError(f"Cannot instantiate {self!r}")

    def __instancecheck__(self, obj):
        raise TypeError(f"{self} cannot be used with isinstance()")

    def __subclasscheck__(self, cls):
        raise TypeError(f"{self} cannot be used with issubclass()")

    @_tp_cache
    def __getitem__(self, parameters):
        item = _type_check(parameters, "Static accepts only single type.")
        return _GenericAlias(self, (item,))


Constant = SubscriptableAlias("Constant", "Constant marker used by nibbler.")
