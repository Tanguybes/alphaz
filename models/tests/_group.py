import inspect

from ._method import TestMethod
from ._wrappers import TEST_METHOD_NAME

from typing import Dict

from collections import OrderedDict

class TestGroup():
    def __init__(self,name,classObject):
        self.name           = name.replace('_Tests','').replace('_tests','')
        self.classObject    = classObject
        self.tests: OrderedDict[str,TestMethod] = OrderedDict()
        self.category       = classObject.category
        if self.category == '':
            self.category = classObject.__module__.split('.')[-1].capitalize() 

        for method_name, method in inspect.getmembers(classObject):
            if '__' in method_name: continue
            if not  inspect.isfunction(method): continue
            if not hasattr(classObject, method.__name__): continue

            method_name = method.__name__
            qual_name = method.__qualname__
            if method_name == TEST_METHOD_NAME or TEST_METHOD_NAME in qual_name:
                test_function                   = TestMethod(classObject,method_name,method,self.category,self.name)
                self.tests[test_function.name]  = test_function

    def get_from_database(self):
        for test in self.tests.values():
            test.get_from_database()

    def test(self,name):
        if name in self.tests:
            self.tests[name].test()

    def test_all(self):
        classObject = self.classObject()
        for method in self.tests.values():
            method.test(classObject=classObject)

    def save_all(self):
        for method in self.tests.values():
            method.save()

    def get_tests_names(self):
        return list(self.tests.keys())

    def print(self,output=True):
        txt = ""
        for test_name, test_def in self.tests.items():
            txt += '{:60} {:4}'.format(test_name,test_def.print()) + '\n'
        if output:
            print(txt)
        return txt

    def to_json(self):
        return self.tests


