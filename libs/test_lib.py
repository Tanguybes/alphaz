import os
from ..models.tests import TestGroups, TestGroup
import importlib
from inspect import getmembers, isfunction, isclass

def get_tests_auto(test_directory,rejects=[]):
    #if test_directory:
    #test_directory = os.path.basename(os.path.dirname(os.path.realpath(__file__)))

    test_groups = TestGroups()

    #test_dir    = test_root + os.sep + test_directory

    for path in os.listdir(test_directory):
        if not path in rejects and not '__' in path and '.py' in path:          
            file_name           = path.replace('.py','')
            import_name         = "%s.%s"%(test_directory.replace('/','.'),file_name)
            module              = importlib.import_module(import_name)
            
            functions_list      = [o for o in getmembers(module) if isclass(o[1]) and '_tests' in o[0].lower()]

            for el in functions_list:
                test_groups.set_test_group(TestGroup(file_name, el[0],el[1]))
    return test_groups

def execute_all_tests_auto(directory,output=True,verbose=False):
    tests_groups = get_tests_auto(directory)
    tests_groups.test_all(verbose=verbose)
    return tests_groups.print(output=output)