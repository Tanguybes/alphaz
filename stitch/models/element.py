from enum import Enum

class Types(Enum):
    INPUT = "input"

class Element():
    id      = None
    etype   = None
    value   = None

    def __init__(self,id, value, etype=None):
        self.id     = id
        self.value  = value
        self.type   = etype

data = {'wpName1':"duranda1", 
        'wpPassword1':'STAdama21it$7', 
        'wpRemember':''} 
