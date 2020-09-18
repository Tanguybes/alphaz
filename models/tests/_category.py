from typing import Dict

from ._group import TestGroup

class TestCategory():
    def __init__(self,category):
        self.category = category

        self.groups: Dict[str,TestGroup] = {}

    def add_test_group(self,testGroup:TestGroup):
        self.groups[testGroup.name]   = testGroup 

    def test_all(self,verbose=False):
        for group_name, test_group in self.groups.items():   
            if test_group.is_verbose():
                print('\n__________ %s __________\n\n'%group_name)
            test_group.test_all(verbose=verbose)

    def save_all(self,verbose=False):
        for group_name, test_group in self.groups.items():   
            if test_group.is_verbose():
                print('\n__________ %s __________\n\n'%group_name)
            test_group.save_all(verbose=verbose)

    def print(self,output=True):
        txt = ""
        for group_name, test_group in self.groups.items():   
            txt += '\n__________ %s __________\n\n'%group_name
            txt += test_group.print(output=False)
        if output:
            print(txt)
        return txt

    def get_tests_groups_names(self):
        return list(self.groups.keys())

    def get_test_group(self,name):
        return self.groups[name]

    def to_json(self):
        return self.groups

class TestCategories():
    def __init__(self):
        self.categories: Dict[str,TestCategory] = {}

    def add_test_group(self,test_group:TestGroup):
        if not test_group.category in self.categories:
            self.categories[test_group.category] = TestCategory(test_group.category)
        
        self.categories[test_group.category].add_test_group(test_group)

    def to_json(self):
        return self.categories
