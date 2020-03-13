
import  os, json, inspect, copy

from ..libs import converter_lib, sql_lib
from ..utils.logger import AlphaLogger, get_alpha_logs_root
from .utils import merge_configuration, get_parameters

PAREMETER_PATTERN = '{{%s}}'

def ensure_path(dict_object,paths=[],value=None):
    if len(paths) == 0: 
        return

    if not paths[0] in dict_object:
        dict_object[paths[0]] = {}

    if len(paths) == 1 and value is not None:
        dict_object[paths[0]] = value
        return

    ensure_path(dict_object[paths[0]],paths[1:],value=value)

class AlphaConfig():
    filename    = None
    exist       = False

    data_origin = {}
    data        = {}
    data_env    = {}

    databases   = {}

    def __init__(self,name='config',filepath=None,root=None,filename=None,log=None,configuration=None,logger_root=None):
        if filepath is not None:
            if not filepath[-5:] == '.json':
                filepath = filepath + '.json'

            filename    = os.path.basename(filepath).split('.')[0]
            if root is None:
                root        = os.path.abspath(filepath).replace('%s.json'%filename,'')
            if name == 'config':
                name    = filename

        if root is None:
            stack       = inspect.stack()
            parentframe = stack[1]
            module      = inspect.getmodule(parentframe[0])
            root        = os.path.abspath(module.__file__).replace(module.__file__,'')
        
        if log is None:
            logger_root = 'logs' if logger_root is None else logger_root
            log         = AlphaLogger(type(self).__name__,type(self).__name__.lower(),root=logger_root)
        self.log        = log

        if filename is None:
            filename = name.lower()
        self.filename = filename

        self.config_file = root + os.sep + self.filename + '.json' if root.strip() != '' else self.filename + '.json'

        self.log.info('Setting config file from %s'%self.config_file)
        if not os.path.isfile(self.config_file):
            self.log.error('Config file %s does not exist !'%self.config_file)
            return

        self.exist = True

        self.load(configuration)

    def load(self,configuration):
        with open(self.config_file) as json_data_file:
            self.data_origin = json.load(json_data_file)

        if "configurations" in self.data_origin:
            configurations = self.data_origin["configurations"]
            
            default_configuration = None
            if "configuration" in self.data_origin:
                default_configuration = self.data_origin['configuration']

            if configuration is not None and configuration in configurations:
                self.data_env = configurations[configuration]
            elif default_configuration is not None and default_configuration in configurations:
                self.data_env = configurations[default_configuration]

        self.init_data()

    def save(self):
        with open(self.config_file,'w') as json_data_file:
            json.dump(self.data_origin,json_data_file, sort_keys=True, indent=4)
            
    def set_data(self,value,paths=[]):
        ensure_path(self.data_origin,paths,value=value)

    def isParameterPath(self,parameters,data=None):
        if data is None:
            data = self.data
        if len(parameters) == 0:
            return True
        if parameters[0] not in data:
            return False
        return self.isParameterPath(parameters[1:],data[parameters[0]])

    def isPath(self,parameters,data=None):
        return self.isParameterPath(parameters,data=data)

    def init_data(self):
        config      = copy.deepcopy(self.data_origin)
        config_env  = copy.deepcopy(self.data_env)
        merge_configuration(config,config_env,replace=True)

        """for p,v in config.items():
            print('   {:20} {}'.format(p,str(v)))

        print('    ENV')
        for p,v in config_env.items():
            print('   {:20} {}'.format(p,str(v)))"""

        structure = {'name':None,'mandatory':True,'value':None}
        if 'databases' in config:

            for database, cf_db in config["databases"].items():
                content_dict = {
                    "user": {},
                    "password": {},
                    "host": {},
                    "name": {'mandatory':False},
                    "port": {},
                    "sid": {'mandatory':False},
                    "database_type": {'name':'type'}
                }

                valid = True
                for name, content in content_dict.items():
                    for key, el in structure.items():
                        if not key in content:
                            if key == 'name':
                                el = name
                            content_dict[name][key] = el

                    if content_dict[name]['name'] in cf_db:
                        content_dict[name]['value'] = cf_db[content_dict[name]['name']]
                    elif content_dict[name]['mandatory']:
                        print('Missing %s parameter'%name)
                        valid = False
                
                fct_kwargs = {x:y['value'] for x,y in content_dict.items()}

                if valid:
                    self.databases[database] = sql_lib.get_connection_from_infos(**fct_kwargs)
                else:
                    self.log.error('Cannot configure database %s'%database)

        self.data = replace_parameters(config)

    def get(self,path=[]):
        if path == '':
            return self.data
        if type(path) == str:
            values, paths = search_it(self.data, path, path=None)
            if len(values) != 0:
                return values[0]
        return self.getParameterPath(path)

    def getParameterPath(self,parameters,data=None):
        if data is None:
            data = self.data

        if parameters[0] not in data:
            return None
        if len(parameters) == 1:
            return data[parameters[0]]

        return self.getParameterPath(parameters[1:],data[parameters[0]])

    def get_connection(self,name):
        if name in self.databases:
            return self.databases[name]
        return None

def set_path(config,path,parameters,parameters_values):
    if len(path) == 1:
        value   = config[path[0]] 
        for parameter in parameters:
            #print(parameter,parameters_values)
            if parameter in parameters_values:
                value = value.replace(PAREMETER_PATTERN%parameter,parameters_values[parameter])
        config[path[0]] = value
        return

    sub_config  = config[path[0]]
    path        = path[1:]

    set_path(sub_config,path,parameters,parameters_values)

def fill_config(configuration,source_configuration):
    for key, value in configuration.items():
        for key2, value2 in source_configuration.items():
            if type(value) != dict and PAREMETER_PATTERN%key2 in str(value):
                value = str(value).replace(PAREMETER_PATTERN%key2,value2)
        configuration[key] = value

def process_configuration(configuration,source_configuration,path=None):
    if path is None:
        fill_config(configuration,source_configuration)

        for key in source_configuration:
            fill_config(configuration,source_configuration[key])

        source  = source_configuration[keys[level]]

        fill_config()

def search_it(nested, target,path=None):
    found, paths = [], []
    if path is None:
        path = []

    for key, value in nested.items():
        next_path = copy.copy(path)
        next_path.append(key)

        if key == target:
            found.append(value)
            paths.append(path)
        
        if isinstance(value, dict):
            f, p = search_it(value, target,next_path)
            found.extend(f)
            paths.extend(p)
        elif isinstance(value, list):
            i = 0
            for item in value:
                if isinstance(item, dict):
                    path.append(i)
                    f, p = search_it(item, target, next_path)
                    found.extend(f)
                    paths.extend(p)
                """else:
                    if key == target:
                        path.append(key)
                        found.append(value)"""
                i += 1
    return found, paths

def get_parameters_from_config(nested, path=None):
    found, paths = [], []
    if path is None:
        path = []

    for key, value in nested.items():
        next_path = copy.copy(path)
        next_path.append(key)

        if isinstance(value, str):
            parameters = get_parameters(value)
            if len(parameters) != 0:
                found.append([ x.replace('{{','').replace('}}','') for x in parameters])
                paths.append(next_path)
        
        if isinstance(value, dict):
            f, p = get_parameters_from_config(value, next_path)
            found.extend(f)
            paths.extend(p)
        elif isinstance(value, list):
            i = 0
            for item in value:
                if isinstance(item, dict):
                    path.append(i)
                    f, p = get_parameters_from_config(item, next_path)
                    found.extend(f)
                    paths.extend(p)
                i += 1
    return found, paths

def get_values_for_parameters(config, parameter_name,path=None):
    """Get the values associated to the parameter in the configuration
    
    Arguments:
        config {json dict} -- configuration as a json dict 
        parameter_name {str} -- parameter_name to search
    
    Keyword Arguments:
        path {list} -- the current path in the json dict as a list (default: {None})
    
    Returns:
        tuple -- a tuple of the parameter values and the parameter path
    """
    found, paths = [], []
    if path is None:
        path = []

    for key, value in config.items():
        next_path = copy.copy(path)
        next_path.append(key)

        if key == parameter_name:
            found.append(value)
            paths.append(path)
        
        if isinstance(value, dict):
            f, p = search_it(value, parameter_name, next_path)
            found.extend(f)
            paths.extend(p)
        elif isinstance(value, list):
            i = 0
            for item in value:
                if isinstance(item, dict):
                    path.append(i)
                    f, p = search_it(item, parameter_name, next_path)
                    found.extend(f)
                    paths.extend(p)
                i += 1
    return found, paths

def replace_parameters(config):
    """Replace parameters formatted has {{<parameter>}} by their values in a json dict
    
    Arguments:
        config {dict} -- json dict to analyse and replace parameters formatted has {{<parameter>}}
    
    Returns:
        dict -- the input dict with parameters replace by their values
    """
    parameters_values, paths = get_parameters_from_config(config, path=None)
    parameters = []
    for i in range(len(parameters_values)):
        parameters.extend(parameters_values[i])

    parameters = list(set(parameters))
    parameters_value = {}
    for parameter in parameters:
        values = search_it(config,parameter)
        if len(values) != 0 and len(values[0]) != 0:
            print(values)
            value = values[0][0]
            parameters_value[parameter] = value

    for i in range(len(parameters_values)):
        set_path(config, paths[i], parameters_values[i], parameters_value)
    return config