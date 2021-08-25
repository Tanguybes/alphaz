from enum import Enum

class Operators(Enum):
    EQUAL = "=="
    ASIGN = "="
    DIFFERENT = "!="
    NOT = "!"
    LIKE = "%"
    NOT_LIKE = "!%"
    SUPERIOR = ">"
    INFERIOR = "<"
    SUPERIOR_OR_EQUAL = ">="
    INFERIOR_OR_EQUAL = "<="
    IN = "in"
    NOT_IN = "notin"