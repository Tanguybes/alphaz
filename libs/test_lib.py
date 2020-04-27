import os, imp, sys, inspect
from ..models.tests import TestGroups, TestGroup, AlphaTest, test
import importlib
from inspect import getmembers, isfunction, isclass
from .py_lib import reload_modules

def get_tests_auto(test_directory,rejects=[],name=None,group=None,import_path=None,log=None):
    #if test_directory:
    #test_directory = os.path.basename(os.path.dirname(os.path.realpath(__file__)))

    test_groups = TestGroups()

    #test_dir    = test_root + os.sep + test_directory
    if log is not None:
        log.info('Loading tests in %s'%(os.getcwd() + os.sep + test_directory))   

    test_groups_directories = os.listdir(test_directory)
    if len(test_groups_directories) == 0:
        if log is not None:
            log.error('No tests files !')

    for path in test_groups_directories:
        if not path in rejects and not '__' in path and '.py' in path:    
            file_name           = path.replace('.py','')
            if name is not None and file_name != name:
                continue
            if log is not None:
                log.info('Get "%s" tests'%file_name)   

            import_name         = "%s.%s"%(test_directory.replace('/','.'),file_name) if import_path is None else import_path + '.' + file_name

            module              = importlib.import_module(import_name)
            importlib.reload(module)
            
            class_list = []
            for o in getmembers(module):
                is_class    = isclass(o[1])
                if is_class:
                    is_test = 'AlphaTest' in str(o[1].__bases__[0])
                    if is_test:
                        class_list.append(o)

            #class_list      = [o for o in getmembers(module) if isclass(o[1]) and '_tests' in o[0].lower()]

            for el in class_list:
                test_group = TestGroup(file_name, el[0],el[1])
                if group is None or group == test_group.name:
                    if log is not None:
                        log.info('Found function group %s'%test_group.name)   
                    test_groups.set_test_group(test_group)

    return test_groups

def execute_all_tests_auto(directory,output=True,verbose=False,refresh=True,name=None):
    return operate_all_tests_auto(directory,output=output,verbose=verbose,refresh=refresh,name=name,
        action='execute')

def save_all_tests_auto(directory,output=True,verbose=False,refresh=True,name=None):
    return operate_all_tests_auto(directory,output=output,verbose=verbose,refresh=refresh,name=name,
        action='save')

def operate_all_tests_auto(directory,output=True,verbose=False,refresh=True,name=None,action='execute',group=None,import_path=None,log=None):
    if refresh:
        reload_modules(os.getcwd(),verbose=False)

    tests_groups = get_tests_auto(directory,group=group,import_path=import_path,log=log)

    if action == 'execute':
        tests_groups.test_all(verbose=verbose)
        return tests_groups.print(output=output)
    elif action == 'save':
        tests_groups.save_all(verbose=verbose)