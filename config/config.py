
import  os, json, inspect, copy

from ..libs import converter_lib, sql_lib
from ..utils.logger import AlphaLogger, get_alpha_logs_root
from .utils import merge_configuration

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

        if 'databases' in config:
            for database, cf_db in config["databases"].items():
                content_list = ["user","pwd","host","port","type"]
                valid = True
                for content in content_list:
                    if not content in cf_db:
                        valid = False

                if valid:
                    self.databases[database] = sql_lib.get_connection_from_infos(
                        user=cf_db['user'], 
                        password=cf_db['pwd'], 
                        host=cf_db['host'],
                        database=cf_db['host'],
                        port=cf_db['port'], 
                        sid=cf_db['sid'],
                        database_type=cf_db['type']
                    )
                else:
                    self.log.error('Cannot configure database %s'%database)

        self.data = config

    def get(self,path=[]):
        if path == '':
            return self.data
        if type(path) == str:
            path = [path]
        return self.getParameterPath(path)

    def getParameterPath(self,parameters,data=None):
        if data is None:
            data = self.data

        if parameters[0] not in data:
            return None
        if len(parameters) == 1:
            return data[parameters[0]]

        return self.getParameterPath(parameters[1:],data[parameters[0]])

pattern = '{{%s}}'
def fill_config(configuration,source_configuration):
    for key, value in configuration.items():
        for key2, value2 in source_configuration.items():
            if type(value) != dict and pattern%key2 in str(value):
                value = str(value).replace(pattern%key2,value2)
        configuration[key] = value

def process_configuration(configuration,source_configuration,path=None):
    if path = None:
        fill_config(configuration,source_configuration)

        for key in source_configuration:
            fill_config(configuration,source_configuration[key])

        source  = source_configuration[keys[level]]

        fill_config()

def search_it(nested, target):
    found = []
    for key, value in nested.iteritems():
        if key == target:
            found.append(value)
        elif isinstance(value, dict):
            found.extend(search_it(value, target))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    found.extend(search_it(item, target))
        else:
            if key == target:
                found.append(value)
    return found