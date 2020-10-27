import os, imp, sys, inspect
from ..models.tests import TestGroup, AlphaTest, test, TestCategories
import importlib
from inspect import getmembers, isfunction, isclass
from .py_lib import reload_modules

from ..utils.logger import AlphaLogger
from typing import List

from core import core
LOG = core.get_logger('tests')

def get_tests_auto(
        tests_modules:List[str],
        name:str=None,
        group:str=None,
        category:str=None,
        run:bool=False,
        log:AlphaLogger=None
    ) -> TestCategories:
    """Get the TestCategories class, containings all required tests

    Args:
        tests_modules (List[str]): list of test modules path
        name (str, optional): the name of the test to select. Defaults to None.
        group (str, optional): the name of the group to select. Defaults to None.
        category (str, optional): the name of the category to select. Defaults to None.
        log (AlphaLogger, optional): the logger. Defaults to None.
        verbose (bool, optional): [description]. Defaults to False.

    Returns:
        TestCategories: [description]
    """
    if not log: log = LOG

    test_categories = TestCategories()

    for tests_module in tests_modules:
        try:
            log.error('Loading test module <%s>'%tests_module)
            module              = importlib.import_module(tests_module)
        except Exception as ex:
            log.error('Cannot load test module <%s>'%tests_module,ex=ex)
            continue

        importlib.reload(module)

        class_list = []
        for o in getmembers(module):
            is_class    = isclass(o[1])
            if is_class:
                is_test = 'AlphaTest' in str(o[1].__bases__[0])
                if is_test:
                    class_list.append(o)

        for el in class_list:
            test_group = TestGroup(el[0],el[1])

            if category is not None and category != test_group.category: continue

            if group is not None and group != test_group.name: continue

            if log is not None: log.info('Found function group %s'%test_group.name)

            if run and name is None:
                test_group.test_all()
            elif run:
                test_group.test(name)
            else:
                test_group.get_from_database()

            test_categories.add_test_group(test_group)

    return test_categories


def execute_all_tests_auto(directory,output=True,verbose=False,refresh=True,name=None,log=None):
    return operate_all_tests_auto(directory,output=output,verbose=verbose,refresh=refresh,name=name,log=log,
        action='execute')

def save_all_tests_auto(directory,output=True,verbose=False,refresh=True,name=None):
    return operate_all_tests_auto(directory,output=output,verbose=verbose,refresh=refresh,name=name,log=log,
        action='save')

def operate_all_tests_auto(directory,output=True,verbose=False,refresh=True,name=None,action='execute',group=None,import_path=None,log=None):
    if refresh:
        reload_modules(os.getcwd(),verbose=False)

    test_categories = get_tests_auto(directory,group=group,import_path=import_path,log=log)

    if action == 'execute':
        tests_groups.test_all(verbose=verbose)
        return tests_groups.print(output=output)
    elif action == 'save':
        tests_groups.save_all(verbose=verbose)