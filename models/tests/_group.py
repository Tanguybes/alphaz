import inspect

from ._method import TestMethod
from ._wrappers import TEST_METHOD_NAME

class TestGroup():
    name        = ""
    classObject = None
    tests       = {}
    verbose     = False

    def __init__(self,name,classObject):
        self.name           = name.replace('_Tests','').replace('_tests','')
        self.classObject    = classObject
        self.tests          = {}
        self.category       = classObject.category

        for method_name, method in classObject.__dict__.items():
            if '__' in method_name: continue
            if inspect.isfunction(method) and method.__name__ == TEST_METHOD_NAME:
                #print('>',method_name,method.__name__)

                test_function                   = TestMethod(classObject,method_name,method)
                self.tests[test_function.name]  = test_function

    def test_all(self,verbose=False):
        self.classObject.verbose = verbose
        for method in self.tests.values():
            method.test(verbose=verbose)

    def save_all(self,verbose=False):
        for method in self.tests.values():
            method.save(verbose=verbose)

    def get_tests_names(self):
        return list(self.tests.keys())

    def print(self,output=True):
        txt = ""
        for test_name, test_def in self.tests.items():
            txt += '{:60} {:4}'.format(test_name,test_def.print()) + '\n'
        if output:
            print(txt)
        return txt

    def is_verbose(self):
        return self.classObject.verbose

    def to_json(self):
        return list(self.tests.keys())


