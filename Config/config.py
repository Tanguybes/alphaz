
import configparser

from ..imports import *
from ..Libs import converter_lib

CONFIG_FILE_EXTENSION                   = '.ini'
CONFIG_DIRECTORY                        = os.path.dirname(os.path.realpath(__file__))

DEFAULTS_VALUES_HEADER                  = 'LibsP'
DEFAULTS_VALUES_HEADER_TEST             = 'Test'

def convert_config_value(value):
    if type(value) != str:
        return value

    valueStr    = str(value).upper()
    
    rangeMatch  = re.match('\[(.*:.*)\]', str(value))
    listMatch   = re.match('\[(.*)\]', str(value))
    dictMatch   = re.match('\{(.*)\}', str(value))

    stringMatchQuote, stringMatch = False, False
    if len(valueStr) != 0:
        stringMatchQuote    = valueStr[0] == '"' and valueStr[-1] == '"' 
        stringMatch         = valueStr[0] == "'" and valueStr[-1] == "'" if not stringMatchQuote else stringMatchQuote
    #stringMatch = re.match('\'(.*)\'',str(value))
        
    if rangeMatch:
        match       = listMatch.groups()[0]
        values      = match.split(':')
        step        = 1 if len(values) == 2 else convert_config_value(values[2])
        value       = np.arange(convert_config_value(values[0]),convert_config_value(values[1])+step,step)
    elif listMatch:
        match       =  listMatch.groups()[0]
        listValues  = match.split(',')
        value       = [convert_config_value(x.lstrip()) for x in listValues]
    elif dictMatch:
        match       = dictMatch.groups()[0]
        listValues  = match.split(',')
        value       = {}
        for el in listValues:
            key, vl = str(el).split(':')
            value[convert_config_value(key)] = convert_config_value(vl)
    elif ':' in valueStr:
        values      = valueStr.split(':')
        step        = 1 if len(values) == 2 else convert_config_value(values[2])
        value       = np.arange(convert_config_value(values[0]),convert_config_value(values[1])+step,step)
    elif ',' in valueStr:
        listValues  = valueStr.split(',')
        value       = [convert_config_value(x.lstrip()) for x in listValues]
    elif stringMatch:
        #match = stringMatch.groups()[0]
        #value = match.replace('\'','')
        value       = value[1:-1]
    elif valueStr == "NONE" or valueStr is None:
        value       = None
    elif valueStr == "FALSE":
        value       = False
    elif valueStr == "TRUE":
        value       = True
    elif valueStr == "FLOAT":
        value       = float
    elif valueStr == "INT":
        value       = int
    elif valueStr == "BOOL":
        value       = bool
    elif valueStr == "STR":
        value       = str
    else:
        value       = converter_lib.to_num(value)
        
    if value is not None and type(value) == str:
        value       = value
    
    return value

def convert_config_value_for_write(value):
    value               = convert_config_value(value)

    if type(value) == str:
        if not value[0] == '"' and not value[0] == "'":
            value       = "'" + value
        if not value[-1] == '"' and not value[-1] == "'":
            value       += "'"
        value           = value.replace('\n','<br>')
    return value

def get_config_filename(fileName,test=False,directory=''):
    prefix                                      = "test_" if test else ""
    parametersFileName                          = "%s/%s%s"%(CONFIG_DIRECTORY,directory + '/' if directory != '' else '',prefix + fileName + CONFIG_FILE_EXTENSION)
    return parametersFileName

def get_config_from_file(fileName,test=False,directory='',verbose=False):
    config                                      = configparser.RawConfigParser()
    config.optionxform                          = str
    
    parametersFileName                          = get_config_filename(fileName,test,directory=directory)
        
    if not os.path.isfile(parametersFileName):
        log.error("Cannot find configuration file at %s (%s)"%(parametersFileName,CONFIG_DIRECTORY))
        exit()
        return None
    
    if verbose:
        log.info("Reading config file: %s"%parametersFileName)

    config.read(parametersFileName)
    return config

def read_parameters_from_config(fileName,config,sectionHeader,test=False,directory=CONFIG_DIRECTORY):
    PARAMETERS                                  = dict()

    if not sectionHeader:
        for section in config.sections():
            for options in config.options(section):
                PARAMETERS[options]             = convert_config_value(config.get(section, options).replace('\n',''))
        
        if test:
            baseParameters                      = load_config_file(fileName,directory=directory,test=False)
        
            for baseParameter, value in baseParameters.items():
                if not baseParameter in PARAMETERS:
                    PARAMETERS[baseParameter]   = value
    else:
        for section in config.sections():
            PARAMETERS[section] = dict()
            for options in config.options(section):
                value = config.get(section, options)
                value = value.replace('\n','') if type(value) == str else value
                PARAMETERS[section][options]    = convert_config_value(value)
        
        if test:
            baseParameters                      = load_config_file(fileName,directory=directory,sectionHeader=True,test=False)
        
            for section, baseParameter in baseParameters.items():
                for baseParameterName, value in baseParameter.items():
                    if not baseParameterName in PARAMETERS[section].keys():
                        PARAMETERS[section][baseParameterName]   = value   
    return PARAMETERS

def load_config_file(fileName,sectionHeader=False,test=False,directory=''):
    if fileName is None:
        return {}
    config = get_config_from_file(fileName,test=test,directory=directory)
    if config is None:
        return {}

    PARAMETERS = read_parameters_from_config(fileName,config,sectionHeader,test=False,directory=directory)
    return PARAMETERS

def write_config_files(fileName,values,test=False,directory=CONFIG_DIRECTORY):
    sectionHeader                               = type(values[list(values.keys())[0]]) == dict
    values                                      = dict(sorted(values.items()))
    
    # Add existing values
    existingConfig                              = load_config_file(fileName,sectionHeader=sectionHeader)
    
    if not sectionHeader:
        for key, value in existingConfig.items():
            if not key in values.keys():
                log.info("Value <%s> is not present in the new configuration settings"%key)
                values[key]                         = value
    else:
        keys = []
        for header, parameter in values.items():
            for key, value in parameter.items():
                keys.append(key)

        for header, parameter in existingConfig.items():
            for key, value in parameter.items():
                if not key in keys:
                    log.info("Value <%s> is not present in the new configuration settings for header <%s>"%(key,header))
                    values[header][key]             = value

    # Set config file
    parametersFileName                          = get_config_filename(fileName,test,directory=directory)
    
    config                                      = configparser.RawConfigParser()
    
    if not sectionHeader:
        header                                  = DEFAULTS_VALUES_HEADER if not test else DEFAULTS_VALUES_HEADER_TEST
    
        config.add_section(header)
        for key, value in values.items():
            value = convert_config_value_for_write(value)
            config.set(header,key,value)
    else:
        for header, parameter in values.items():
            config.add_section(header)
            for key, value in parameter.items():
                value = convert_config_value_for_write(value)
                config.set(header,key,value)
    
    with open(parametersFileName, 'w') as configfile:
        config.write(configfile)

def write_defaults_config_files(fileName,values,directory=CONFIG_DIRECTORY):
    # Add existing values
    #     existingConfig                              = load_config_file(fileName,directory=directory,sectionHeader=True)
    existingConfig = get_config_from_file(fileName,directory=directory)
        
    # Set config file
    parametersFileName                          = get_config_filename(fileName,directory=directory)
        
    for header, value in values.items():
        existingConfig.set(header,'value',value)

    with open(parametersFileName, 'w') as configfile:
        existingConfig.write(configfile)
        
    PARAMETERS = read_parameters_from_config(fileName,existingConfig,sectionHeader=True,test=False,directory=directory)

def write_menu_defaults_config_files(fileName,values,test=False,directory=CONFIG_DIRECTORY):
    values = dict(sorted(values.items()))
    
    # Add existing values
    existingConfig                              = load_config_file(fileName,directory=directory,sectionHeader=False,test=test)
    
    for key, value in existingConfig.items():
        if not key in values.keys():
            values[key]                         = value
    
    # Set config file
    parametersFileName                          = get_config_filename(fileName,test,directory=directory)
    
    config                                      = configparser.RawConfigParser()
    
    header                                      = DEFAULTS_VALUES_HEADER if not test else DEFAULTS_VALUES_HEADER_TEST
    
    config.add_section(header)
    for key, value in values.items():
        print("value: ",value, " type ",type(value))
        config.set(header,key,value)
    
    with open(parametersFileName, 'w') as configfile:
        config.write(configfile)
        
def get_ordered_intervals(list_intervals):
    return [x for x in Config.getMainConfigValue('intervals_list') if x in list_intervals]
        
class Config(object):
    MAIN_CONFIG_NAME        = "main"
    
    MAIN                    = load_config_file(MAIN_CONFIG_NAME)
    
    @staticmethod
    def getConfigValue(name,config_name):
        config_dict = {}
        
        if config_name == Config.MAIN_CONFIG_NAME:
            config_dict = Config.MAIN
        
        if not name in config_dict.keys():
            print('Missing key <%s> in config <%s>'%(name,config_name))
            log.error('Missing key <%s> in config <%s>'%(name,config_name))
            return None
        
        return config_dict[name]
    
    @staticmethod 
    def getMainConfigValue(name):
        return Config.getConfigValue(name, Config.MAIN_CONFIG_NAME)
        