from opcode import opmap

__all__ = [
    "REVERSE_OPMAP",
    "CALL_FUNCTION",
    "EXTENDED_ARG",
    "LOAD_CONST",
    "LOAD_FAST",
    "LOAD_GLOBAL",
    "POP_JUMP_IF_FALSE",
    "POP_JUMP_IF_TRUE",
    "POP_TOP",
    "RETURN_VALUE",
    "STORE_FAST",
    "LOAD_INSTRUCTIONS",
    "INSTRUCTION_FORMAT",
    "STEP",
    "CODE_TYPE",
    "FUNCTION_TYPE",
]

REVERSE_OPMAP = {value: key for key, value in opmap.items()}

CALL_FUNCTION = opmap["CALL_FUNCTION"]
EXTENDED_ARG = opmap["EXTENDED_ARG"]

LOAD_CONST = opmap["LOAD_CONST"]
LOAD_FAST = opmap["LOAD_FAST"]
LOAD_GLOBAL = opmap["LOAD_GLOBAL"]
LOAD_DEREF = opmap["LOAD_DEREF"]

POP_JUMP_IF_FALSE = opmap["POP_JUMP_IF_FALSE"]
POP_JUMP_IF_TRUE = opmap["POP_JUMP_IF_TRUE"]
POP_TOP = opmap["POP_TOP"]
RETURN_VALUE = opmap["RETURN_VALUE"]
STORE_FAST = opmap["STORE_FAST"]

LOAD_INSTRUCTIONS = [opmap[op] for op in opmap if op.startswith("LOAD_")]

INSTRUCTION_FORMAT = "BB"
STEP = 2

CODE_TYPE = type((lambda: None).__code__)
FUNCTION_TYPE = type(lambda: None)

OP = 0
ARG = 1
