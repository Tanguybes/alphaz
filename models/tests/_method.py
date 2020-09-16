

class TestMethod():
    name        = ""
    method      = None
    valid       = None
    classObject = None

    def __init__(self,classObject,name,method):
        self.name           = name
        self.method         = method
        self.classObject    = classObject
        
    def test(self,verbose=False):
        classObject         = self.classObject()
        classObject.verbose = verbose

        self.valid          = classObject.test(self.name)
        return self.valid

    def save(self,verbose=False):
        classObject         = self.classObject()
        classObject.verbose = verbose

        classObject.save(self.name)

    def is_valid(self):
        return self.valid != None and self.valid

    def print(self):
        return 'OK' if self.valid else 'X'