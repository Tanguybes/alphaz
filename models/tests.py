import os, inspect
from functools import wraps

from ..libs.io_lib import archive_object, unarchive_object

test_method_name = 'test_call'
class test(object):
    def __init__ (self, *args, **kwargs):
        # store arguments passed to the decorator
        self.args = args
        self.kwargs = kwargs

    def __call__(self, func):
        def test_call(*args, **kwargs):
            #the 'self' for a method function is passed as args[0]
            slf = args[0]

            # replace and store the attributes
            saved = {}
            for k,v in self.kwargs.items():
                if hasattr(slf, k):
                    saved[k] = getattr(slf,k)
                    setattr(slf, k, v)

            # call the method
            ret = func(*args, **kwargs)

            #put things back
            for k,v in saved.items():
                setattr(slf, k, v)

            return ret
        test_call.__doc__ = func.__doc__
        return test_call 

"""def test(save=False):
    def test_alpha_in(func):
        def test_wrapper(*args,**kwargs):
            return func(*args, **kwargs)
        print('exe',func)
        test_wrapper.__name__ = func.__name__
        return test_wrapper
    return test_alpha_in"""

class AlphaSave():
    root    = None
    ext     = '.ast'
    
    @staticmethod
    def set_root(root):
        AlphaSave.root = root

    @staticmethod
    def get_file_path(filename):
        file_path = AlphaSave.root + os.sep + filename + '.ast'
        return file_path

    @staticmethod
    def save(object_to_save,filename):
        file_path = AlphaSave.get_file_path(filename)
        directory = os.path.dirname(file_path)
        os.makedirs(directory,exist_ok=True)
        archive_object(object_to_save,file_path)

    @staticmethod
    def load(filename):
        file_path = AlphaSave.get_file_path(filename)
        return unarchive_object(file_path)


save_method_name = "save_method_result"  
def save(func):
    def save_method_result(*args, **kwargs):  
        get_return, get_name = False, False
        new_kwargs = {}
        args = list(args)
        #print('must-have arguments are:')
        """for i in args:
            print(i)   """       
        #print('optional arguments are:')
        for kw in kwargs.keys():
            #print( kw+'='+str( kwargs[kw] ) )
            if kw == "get_return":
                get_return = True
            elif kw == "get_name":
                get_name = True
            else:
                new_kwargs[kw] = kwargs[kw]

        return_save = AlphaSave.load(func.__name__)

        if get_return:
            return func(*args, **new_kwargs)
        elif get_name:
            return func.__name__
        else:
            return func(*args, **new_kwargs) == return_save
    return save_method_result

class AlphaTest():
    verbose = False
    output  = True
    
    def __init__(self,verbose=False):
        self.verbose = verbose

    def test(self,name):
        fct = getattr(self,name)
        if fct is None:
            return False
        return fct()

    def save(self,name):
        fct = getattr(self,name)
        if fct is None:
            return False
            
        if inspect.unwrap(fct).__name__ == save_method_name:
            object_to_save      = fct(get_return=True)
            object_name_to_save = fct(get_name=True)
            AlphaSave.save(object_to_save,object_name_to_save)

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
            if inspect.isfunction(method) and method.__name__ == test_method_name:
                #print('>',method_name,method.__name__)

                test_function                   = TestFunction(classObject,method_name,method)
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

class TestGroups():
    tests = {}

    def set_test_group(self,testGroup):
        self.tests[testGroup.name]   = testGroup 

    def test_all(self,verbose=False):
        for group_name, test_group in self.tests.items():   
            if test_group.is_verbose():
                print('\n__________ %s __________\n\n'%group_name)
            test_group.test_all(verbose=verbose)

    def save_all(self,verbose=False):
        for group_name, test_group in self.tests.items():   
            if test_group.is_verbose():
                print('\n__________ %s __________\n\n'%group_name)
            test_group.save_all(verbose=verbose)

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
