import os, imp, sys, inspect
from ..models.tests import TestGroup, AlphaTest, test, TestCategories
import importlib
from inspect import getmembers, isfunction, isclass
from .py_lib import reload_modules

from ..models.logger import AlphaLogger
from typing import List

from core import core
LOG = core.get_logger('tests')

CATEGORIES = {}

def get_tests_auto(
        tests_modules:List[str],
        name:str=None,
        group:str=None,
        category:str=None,
        run:bool=False
    ) -> TestCategories:
    """Get the TestCategories class, containings all required tests.

    Args:
        tests_modules (List[str]): list of test modules path
        tests_modules (List[str]): list of test modules path
        name (str, optional): the name of the test to select. Defaults to None.
        group (str, optional): the name of the group to select. Defaults to None.
        category (str, optional): the name of the category to select. Defaults to None.

    Returns:
        TestCategories: [description]
    """
    global CATEGORIES

    test_categories = TestCategories()

    for tests_module in tests_modules:
        try:
            LOG.debug('Loading test module <%s>'%tests_module)
            module              = importlib.import_module(tests_module)
        except Exception as ex:
            LOG.error('Cannot load test module <%s>'%tests_module,ex=ex)
            continue

        #importlib.reload(module)

        class_list = []
        for o in getmembers(module):
            is_class    = isclass(o[1])
            if not is_class: continue
            is_test = issubclass(o[1], AlphaTest) and (not hasattr(o[1],"_test") or o[1]._test) and not o[1] == AlphaTest
            if not is_test: continue
            class_list.append(o)

        for el in class_list:
            test_group = TestGroup(el[0],el[1])

            if category is not None and category != test_group.category: continue

            if group is not None and group != test_group.name: continue

            if LOG is not None: 
                LOG.debug('Found function group <%s>'%test_group.name)

            if run and name is None:
                test_group.test_all()
            elif run:
                test_group.test(name)
            else:
                test_group.get_from_database()

            test_categories.add_test_group(test_group)
    return test_categories


def execute_all_tests_auto(directory,output=True,refresh=True,name=None):
    return operate_all_tests_auto(directory,output=output,refresh=refresh,name=name,
        action='execute')

def save_all_tests_auto(directory,output=True,refresh=True,name=None):
    return operate_all_tests_auto(directory,output=output,refresh=refresh,name=name,
        action='save')

def operate_all_tests_auto(directory,output=True,refresh=True,name=None,action='execute',group=None,import_path=None):
    if refresh:
        reload_modules(os.getcwd())

    test_categories = get_tests_auto(directory,group=group,import_path=import_path)

    if action == 'execute':
        tests_groups.test_all()
        return tests_groups.print(output=output)
    elif action == 'save':
        tests_groups.save_all()