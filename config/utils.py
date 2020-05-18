import re

def merge_configuration(configuration,source_configuration,replace=False,path=[]):
    for key2, value2 in source_configuration.items():
        if not key2 in configuration:
            configuration[key2] = value2
        elif replace:
            if type(value2) == dict:
                path.append(key2)
                merge_configuration(configuration[key2],source_configuration[key2],replace=replace,path=path)
            #elif type(value2) == list:
            else:
                configuration[key2] = value2


def get_parameters(content):
    title_regex = r'\{\{.*?\}\}'
    founds      = re.findall(title_regex,content)
    return founds

def get_mails_parameters(content):
    title_regex = r'\[\[.*?\]\]'
    founds      = re.findall(title_regex,content)
    return founds