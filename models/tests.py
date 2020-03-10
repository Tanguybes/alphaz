from inspect import getmembers, isfunction, isclass

class Test():
    verbose = False
    output  = True
    
    def __init__(self,verbose=False):
        self.verbose = verbose

    def test(self,name):
        fct = getattr(self,name)
        if fct is None:
            return False
        return fct()

    def array_equal(self,a,b):
        equal = len(a) == len(b)
        if equal:
            for i in range(len(a)):
                if a[i] != b[i]: 
                    #if self.verbose:
                    #    print("   {:10} {:20} != {}".format(i,a[i],b[i]))
                    equal = False
        elif self.verbose:
            print("Arrays size are not equal:",len(a),len(b))
        return equal

class TestFunction():
    name        = ""
    raw_name    = ""
    method      = None
    valid       = None
    classObject = None

    def __init__(self,classObject,raw_name,method):
        self.name           = raw_name.lower().replace('test_','')
        self.raw_name       = raw_name
        self.method         = method
        self.classObject    = classObject
        
    def test(self,verbose=False):
        classObject         = self.classObject()
        classObject.verbose = verbose

        self.valid          = classObject.test(self.raw_name)
        return self.valid

    def is_valid(self):
        return self.valid != None and self.valid

    def print(self):
        return 'OK' if self.valid else 'X'

class TestGroup():
    file_name   = ""
    name        = ""
    classObject = None
    tests       = {}
    verbose     = False

    def __init__(self,file_name,raw_name,classObject):
        self.file_name      = file_name
        self.name           = raw_name.replace('_Tests','').replace('_tests','')
        self.classObject    = classObject
        self.tests          = {}

        for method_name, method in classObject.__dict__.items():
            if isfunction(method) and 'test_' in method_name.lower():
                test_function                   = TestFunction(classObject,method_name,method)
                self.tests[test_function.name]  = test_function

    def test_all(self,verbose=False):
        for method in self.tests.values():
            method.test(verbose=verbose)

    def get_tests_names(self):
        return list(self.tests.keys())

    def print(self,output=True):
        txt = ""
        for test_name, test_def in self.tests.items():
            txt += '{:40} {:4}'.format(test_name,test_def.print()) + '\n'
        if output:
            print(txt)
        return txt

    def is_verbose(self):
        return self.classObject.verbose

class TestGroups():
    tests = {}

    def set_test_group(self,testGroup):
        self.tests[testGroup.name]   = testGroup 

    def test_all(self,verbose=False):
        for group_name, test_group in self.tests.items():   
            if test_group.is_verbose():
                print('\n__________ %s __________\n\n'%group_name)
            test_group.test_all(verbose=verbose)

    def print(self,output=True):
        txt = ""
        for group_name, test_group in self.tests.items():   
            txt += '\n__________ %s __________\n\n'%group_name
            txt += test_group.print(output=False)
        if output:
            print(txt)
        return txt

    def get_tests_groups_names(self):
        return list(self.tests.keys())

    def get_test_group(self,name):
        return self.tests[name]
