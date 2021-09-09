from typing import Dict

from ...libs import dict_lib

from ._group import TestGroup

class TestCategory():
    def __init__(self,category):
        self.category = category

        self.groups: Dict[str,TestGroup] = {}

    def add_test_group(self,testGroup:TestGroup):
        self.groups[testGroup.name]   = testGroup 

    def test_all(self):
        for group_name, test_group in self.groups.items():   
            test_group.test_all()

    def save_all(self):
        for group_name, test_group in self.groups.items():   
            test_group.save_all()

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

        self.categories = dict_lib.sort_dict(self.categories)

    def to_json(self):
        return self.categories

    def to_junit(self, file_path):
        if not '.' in file_path:
            file_path += '.xml'
        from junit_xml import TestSuite, TestCase

        suites = []
        for category_name, category in self.categories.items():
            test_cases = []
            for group_name, group in category.groups.items():
                for test_name, test in group.tests.items():
                    stdout = test.last_run_elapsed
                    stderr = str(test.ex) if test.ex is not None else None
                    test_case = TestCase(test_name, group_name, test.elapsed, stdout, stderr, timestamp=test.end_time, status=test.status)
                    if not test.ex:
                        test_case.add_error_info(message=test.ex, error_type=type(test.ex))
                    if not test.status:
                        test_case.add_failure_info(message="failed")
                    test_cases.append(test_case)
            suites.append(TestSuite(category_name, test_cases))
        
        with open(file_path, 'w') as f:
            f.write(TestSuite.to_xml_string(suites))

