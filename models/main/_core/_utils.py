import os

def convert_value_for_environment(value: object) -> str:
    if str(value).lower() == 'true': value = '1'
    elif str(value).lower() == 'false': value = '0'
    return str(value)

def set_environment_variables(environs:dict):
    if environs:
        for key, value in environs.items():
            os.environ[key] = convert_value_for_environment(value)

