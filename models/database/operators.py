from enum import Enum

class Operators(Enum):
    EQUAL = "=="
    ASIGN = "="
    DIFFERENT = "!="
    NOT = "!"
    LIKE = "like"
    NOT_LIKE = "notlike"
    ILIKE = "ilike"
    NOT_ILIKE = "notlike"
    SUPERIOR = ">"
    INFERIOR = "<"
    SUPERIOR_OR_EQUAL = ">="
    INFERIOR_OR_EQUAL = "<="
    IN = "in"
    NOT_IN = "notin"

    def equals(self, string):
       return self.value == string