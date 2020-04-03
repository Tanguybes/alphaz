import os, imp, sys, inspect
from ..models.tests import TestGroups, TestGroup
import importlib
from inspect import getmembers, isfunction, isclass
from .py_lib import reload_modules

def get_tests_auto(test_directory,rejects=[],name=None,group=None):
    #if test_directory:
    #test_directory = os.path.basename(os.path.dirname(os.path.realpath(__file__)))

    test_groups = TestGroups()

    #test_dir    = test_root + os.sep + test_directory

    for path in os.listdir(test_directory):
        if not path in rejects and not '__' in path and '.py' in path:          
            file_name           = path.replace('.py','')
            if name is not None and file_name != name:
                continue

            import_name         = "%s.%s"%(test_directory.replace('/','.'),file_name)
            module              = importlib.import_module(import_name)
            importlib.reload(module)
            
            functions_list      = [o for o in getmembers(module) if isclass(o[1]) and '_tests' in o[0].lower()]

            for el in functions_list:
                test_group = TestGroup(file_name, el[0],el[1])
                if group is None or group == test_group.name:
                    test_groups.set_test_group(test_group)
    return test_groups

def execute_all_tests_auto(directory,output=True,verbose=False,refresh=True,name=None):
    return operate_all_tests_auto(directory,output=output,verbose=verbose,refresh=refresh,name=name,
        action='execute')

def save_all_tests_auto(directory,output=True,verbose=False,refresh=True,name=None):
    return operate_all_tests_auto(directory,output=output,verbose=verbose,refresh=refresh,name=name,
        action='save')

def operate_all_tests_auto(directory,output=True,verbose=False,refresh=True,name=None,action='execute',group=None):
    if refresh:
        reload_modules(os.getcwd(),verbose=False)

    tests_groups = get_tests_auto(directory,group=group)

    if action == 'execute':
        tests_groups.test_all(verbose=verbose)
        return tests_groups.print(output=output)
    elif action == 'save':
        tests_groups.save_all(verbose=verbose)