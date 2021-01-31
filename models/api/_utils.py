from ._requests import get_token_from_request

MAIL_PARAMETERS_PATTERN = '[[%s]]'

def fill_config(configuration,source_configuration):
    for key, value in configuration.items():
        for key2, value2 in source_configuration.items():
            if type(value) != dict and MAIL_PARAMETERS_PATTERN%key2 in str(value):
                value = str(value).replace(MAIL_PARAMETERS_PATTERN%key2,value2)
        configuration[key] = value


def merge_configuration(configuration,source_configuration,replace=False):
    for key2, value2 in source_configuration.items():
        if (not key2 in configuration or replace) and type(value2) != dict:
            configuration[key2] = value2

def get_logged_user():
    user_data = None
    token = get_token_from_request()
    if token is not None:
        from ...apis import users  # todo: modify
        user_data = users.get_user_dataFromToken(token)
    return user_data