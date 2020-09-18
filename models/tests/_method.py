import datetime

class TestMethod():
    def __init__(self,classObject,name:str,method):
        self.name:str           = name
        self.method             = method
        self.classObject  = classObject
        self.valid:bool         = None
        self.start_time         = None
        self.end_time           = None
        self.elapsed            = None
        
    def test(self,verbose=False):
        classObject             = self.classObject()
        classObject.verbose     = verbose

        self.start_time         = datetime.datetime.now()
        self.valid              = classObject.test(self.name)
        self.end_time           = datetime.datetime.now()
        self.elapsed            = self.end_time - self.start_time
        return self.valid

    def save(self,verbose=False):
        classObject         = self.classObject()
        classObject.verbose = verbose
        classObject.save(self.name)

    def is_valid(self):
        return self.valid != None and self.valid

    def print(self):
        return 'OK' if self.valid else 'X'

    def to_json(self):
        return {
            'valid': self.valid,
            'elapsed': self.elapsed
        }