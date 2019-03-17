from .extension import constantize_globals
from .extension import debug  # noqa: F401
from .extension import global_to_fast
from .extension import inline
from .extension import integrity_check
from .extension import map_source
from .extension import peephole
from .extension import precompute_conditionals

__all__ = ["DEFAULT_CONFIG"]

DEFAULT_CONFIG = [
    extension.EXTENSION
    for extension in [
        inline,
        constantize_globals,
        precompute_conditionals,
        global_to_fast,
        integrity_check,
        # Provide well-formed lnotab to peephole optimizer
        map_source,
        peephole,
        map_source,
    ]
]
