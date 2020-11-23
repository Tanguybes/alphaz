import ast

from ._base import AlphaClass

class AlphaTransaction(AlphaClass):
    def __init__(self,obj):
        self.uuid:str = obj.uuid
        self.process:int= obj.process

        try:
            self.message = ast.literal_eval(obj.message)
        except:
            self.message = None
        self.message_type:str = obj.message_type
        self.lifetime:int = obj.lifetime
        self.creation_date:datetime.datetime = obj.creation_date

    @staticmethod
    def get_type(class_):
        name = class_ if type(class_) == str else class_.__class__.__name__
        return [(c if c.upper() != c or i == 0 else "_" + c) for i, c in enumerate(name)]