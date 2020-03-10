

def merge_configuration(configuration,source_configuration,replace=False):
    for key2, value2 in source_configuration.items():
        if (not key2 in configuration or replace):
            configuration[key2] = value2