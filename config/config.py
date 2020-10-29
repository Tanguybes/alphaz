
import  os, json, inspect, copy, sys, socket, re, platform, getpass
import numpy as np
from typing import List, Dict

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from . import utils

from ..libs import converter_lib, sql_lib, io_lib
from ..utils.logger import AlphaLogger
from ..models.main import AlphaClass

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

def ensure_filepath(name:str,filepath:str,root:str,filename:str):
    name = name.split('/')[-1]
    if filepath is not None:    
        if not filepath[-5:] == '.json':
            filepath    = filepath + '.json'

        filename        = os.path.basename(filepath).split('.')[0]
        if root is None:
            root        = os.path.abspath(filepath).replace('%s.json'%filename,'')
        if name == 'config':
            name        = filename

    if root is None:
        stack           = inspect.stack()
        parentframe     = stack[1]
        module          = inspect.getmodule(parentframe[0])
        filename_frame  = parentframe.filename
        current_path    = os.getcwd()
        root            = current_path
    
    if filename is None:
        filename        = name.lower()

    filepath       = root + os.sep + filename + '.json'
    return name, filepath, root, filename

class AlphaConfigurations(object):
    _name = 'configs'
    _instance = None
    _configurations: Dict[str,object] = {}

    def __new__(cls):
        try:
            cls._instance = io_lib.unarchive_object(AlphaConfigurations._name)
        except Exception as ex:
            print(ex)

        if not cls._instance:
            cls._instance = object.__new__(cls)
        return cls._instance

    def get_configuration(self,path:str):
        if path in self._configurations:
            return self._configurations[path]
        return None

    def set_configuration(self,path:str, config):
        self._configurations[path] = config
        io_lib.archive_object(self, self._name)

CONFIGURATIONS = AlphaConfigurations()

class AlphaConfig(AlphaClass):
    reserved    =  ['user']

    def __new__(cls,
            name: str='config',
            filepath: str=None,
            root: str=None,
            filename: str=None,
            log: AlphaLogger=None,
            configuration: str=None,
            logger_root: str=None,
            data: dict=None,
            origin=None
            ):

        name, filepath, root, filename = ensure_filepath(name, filepath, root, filename)
        #key = "%s - %s - %s"%(name,filepath,configuration)

        instance = CONFIGURATIONS.get_configuration(filepath)
        if instance is not None:
            return instance

        instance = super(AlphaConfig, cls).__new__(cls)
        instance.__init__(name, filepath, root, filename, log, configuration, logger_root, data, origin)
        return instance

    def __init__(self,
            name: str = 'config',
            filepath: str = None,
            root: str = None,
            filename: str = None,
            log: AlphaLogger = None,
            configuration: str = None,
            logger_root: str = None,
            data: dict = None,
            origin = None
            ):

        if hasattr(self, 'tmp'): return
        self.name = name
        self.filepath = filepath
        self.root = root
        self.filename = filename
        self.configuration:str = configuration
        self.logger_root = logger_root
        self.origin = origin

        super().__init__(log=log)

        self.tmp         = {}
        self.data_origin = {}

        self.data        = {}
        self.data_env    = {}
        self.data_user   = {}
        self.data_platform = {}
        self.data_ip     = {}

        self.exist       = False
        self.valid       = True
        self.loaded      = False

        self.databases   = {}
        self.loggers     = {}

        self.infos       = []
        self.warnings    = []

        self.db_cnx      = None

        self.api = None
        self.cnx_str = None

        self.log            = log

        if data:
            self.data_origin  = data
            self.data         = data
        else:
            self.load_raw()

        if data is None and configuration is not None:
            self.set_configuration(configuration)

        if configuration is None:
            self.auto_configuration()

        CONFIGURATIONS.set_configuration(self.filepath, self)

    def auto_configuration(self):
        configuration = None
        if 'configuration' in self.data_origin:
            configuration = self.data_origin['configuration']
        elif 'default_configuration' in self.data_origin:
            configuration = self.data_origin['default_configuration']
        if configuration is not None:
            self.set_configuration(configuration)

    def set_configuration(self,configuration):
        if len(self.tmp) != 0:
            self.data_origin = {x:y for x,y in self.data_origin.items() if x not in self.tmp}

        if configuration is None:
            self.error('Configuration need to be explicitely specified in configuration call or config file for %s file'%self.filepath)
            return 

        self.configuration = configuration
        self.info('Setting <%s> configuration for file %s'%(configuration,self.filepath))
                
        if os.path.isfile(self.filepath):
            self.exist = True
            #self.add_tmp('configuration',configuration)
            self.load(configuration)
            self.check_required()
        else:
            self.error('Config file %s does not exist !'%self.filepath)
            exit()

    def get_config(self,path=[],configuration=None):
        path = self.get_path(path)
        config_data = self.get(path)
        if config_data is None:
            return None
            
        # TODO: enhance
        config      = AlphaConfig(
            name    = '.'.join(path), # self.name,
            root    = self.root,
            log     = self.log,
            configuration   = self.configuration if configuration is None else configuration,
            logger_root     = self.logger_root,
            data            = config_data
        )
        return config

    def check_required(self):
        if not 'required' in self.data:
            return

        for path in self.data['required']:
            if not self.is_path(path):
                self.log.error("Missing '%s' key in config file"%('/'.join(path)))
                self.valid = False

    def __check_reserved(self):
        for reserved_name in self.reserved:
            if reserved_name in self.data_origin:
                self.error('"%s" entry in configuration %s is reserved'%(reserved_name,self.filepath))
                exit()

    def add_tmp(self,name,value):
        if name in self.data_origin:
            self.error('<%s> entry in configuration %s is reserved'%(name,self.filepath))
            exit()

        self.tmp[name]          = value
        self.data_origin[name]  = value

    def load_raw(self):
        if not self.loaded:
            with open(self.filepath) as json_data_file:
                self.data_origin = json.load(json_data_file)
                self.loaded = True

    def load(self,configuration):
        try:
            self.load_raw()
        except Exception as ex:
            print('Cannot read configuration file %s:%s'%(self.filepath,ex))
            exit()
        
        self.__check_reserved()

        if "configurations" in self.data_origin:
            configurations = self.data_origin["configurations"]
            
            default_configuration = None
            if "default_configuration" in self.data_origin:
                default_configuration = self.data_origin['default_configuration']

            if configuration is not None and configuration in configurations:
                self.data_env = configurations[configuration]
            elif default_configuration is not None and default_configuration in configurations:
                self.data_env = configurations[default_configuration]

        self.configuration = configuration

        self.add_tmp('configuration',configuration)
        self.add_tmp('run',os.getcwd())
        self.add_tmp('project',os.getcwd())

        user = getpass.getuser()
        user_configured = False
        self.add_tmp('user',user)

        if "users" in self.data_origin:
            users = self.data_origin["users"]
            
            if user in users:
                self.data_user = self.data_origin["users"][user]

        current_ip = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
        ip_configured = False
        self.add_tmp('ip',current_ip)
        if "ips" in self.data_origin:
            ips = self.data_origin["ips"]
            if current_ip in ips:
                self.data_ip = self.data_origin["ips"][current_ip]

        system_platform    = platform.system()
        platform_configured = False
        self.add_tmp('platform',system_platform)
        if "platforms" in self.data_origin:
            platforms = self.data_origin["platforms"]

            if system_platform.lower() in platforms:
                self.data_platform = self.data_origin["platforms"][system_platform.lower()]

        self.init_data()

        if self.core_configuration: 
            self.info('Configuration %s initiated for user <%s%s>, %s%s ip and <%s%s> platform'%(self.filepath,user,'' if not user_configured else "*",current_ip,'' if not ip_configured else "*",system_platform,'' if not platform_configured else "*" ))

    def show(self):
        show(self.data)

    def save(self):
        self.info('Save configuration file at %s'%self.filepath)

        for name in self.tmp:
            if name in self.data_origin:
                del self.data_origin['user']

        with open(self.filepath,'w') as json_data_file:
            json.dump(self.data_origin,json_data_file, sort_keys=True, indent=4)
            
    def set_data(self,value,paths=[]):
        ensure_path(self.data_origin,paths,value=value)

    def is_parameter_path(self,parameters,data=None):
        if type(parameters) == str:
            parameters  = [parameters]
        if data is None:
            data = self.data
        if len(parameters) == 0:
            return True
        if parameters[0] not in data:
            return False
        return self.is_parameter_path(parameters[1:],data[parameters[0]])

    def is_path(self,parameters,data=None):
        return self.is_parameter_path(parameters,data=data)

    def set_sub_configurations(self):
        config = self.data
        # get sub configurations
        sub_configurations = {}
        configs_values, paths = get_configs_from_config(config, path=None)
        for i, values in enumerate(configs_values):
            config_path = values[0]
            if not config_path in sub_configurations:
                name                            = config_path.split(os.sep)[-1]
                sub_configurations[config_path] = AlphaConfig(name=name,filepath=config_path,
                    log=self.log,
                    configuration=self.configuration,
                    logger_root=self.logger_root,
                    origin=self
                )

        # replace sub configurations
        set_paths(config,paths,configs_values,sub_configurations,types='configs')
        self.data = config

    def init_data(self):
        config          = copy.deepcopy(self.data_origin)
        config_env      = copy.deepcopy(self.data_env)
        config_user     = copy.deepcopy(self.data_user)
        config_ip       = copy.deepcopy(self.data_ip)
        config_platform = copy.deepcopy(self.data_platform)
        
        utils.merge_configuration(config,config_ip,replace=True)
        utils.merge_configuration(config,config_platform,replace=True)
        utils.merge_configuration(config,config_user,replace=True)
        utils.merge_configuration(config,config_env,replace=True)

        if 'users' in config:
            del config['users']

        debug = False

        self.replace_parameters(config)
        self.set_sub_configurations()

        if "paths" in config:
            for path in config["paths"]:
                sys.path.append(path)

        self.core_configuration = self.get('core_configuration',root=False)
        if not self.core_configuration:
            return

        # loggers
        self.logger_root = self.get("directories/logs")
        if self.logger_root is None:
            self.error('Missing "directories/logs" entry in configuration file %s'%self.filepath)
            exit()

        colors = self.get("colors/loggers")

        # log
        if self.log is None:
            log_filename        = "alpha" #type(self).__name__.lower()
            self.log            = AlphaLogger(type(self).__name__,log_filename,root=self.logger_root,colors=colors)

        if self.is_path("loggers"):
            for logger_name in self.get("loggers").keys():
                logger_config   = self.get_config(["loggers",logger_name])
                root            = logger_config.get("root")

                if not logger_name in self.loggers:
                    self.loggers[logger_name] = AlphaLogger(
                        logger_name,
                        filename    = logger_config.get("filename"),
                        root        = root if root is not None else self.logger_root,
                        cmd_output  = logger_config.get("cmd_output") or True,
                        level       = logger_config.get("level"),
                        colors      = colors,
                        database    = logger_config.get("database")
                    )

        main_logger_name = "main"
        if not main_logger_name in self.loggers:
            self.log = AlphaLogger(
                main_logger_name,
                root        = self.logger_root,
                cmd_output  = True,
                colors=colors
            )
            self.loggers[main_logger_name] = self.log

        if 'databases' in config:
            self.configure_databases(config["databases"])

        if self.is_path("envs"):
            for env, value in self.get("envs").items():
                os.environ[env] = value

    def configure_databases(self,config):
        # Databases
        structure   = {'name':None,'required':False,'value':None}

        db_cnx      = {}
        for db_name, cf_db in config.items():
            if type(cf_db) == str and cf_db in config:
                cf_db = config[cf_db]
            elif type(cf_db) != dict:
                continue

            # TYPE
            if not "type" in cf_db:
                self.show()
                self.error("Missing <type> parameter in <%s> database configuration"%db_name)

            db_type = cf_db['type']

            content_dict = {
                "user": {},
                "password": {},
                "host": {},
                "name": {},
                "port": {},
                "sid": {},
                "path": {},
                "database_type": {'name':'type'},
                "log": {'default':self.log}
            }
            if db_type == 'sqlite':
                content_dict["path"]['required'] = True
            else:
                content_dict["user"]['required'] = True
                content_dict["password"]['required'] = True
                content_dict["host"]['required'] = True
                content_dict["port"]['required'] = True

            for name, content in content_dict.items():
                for key, el in structure.items():
                    if not key in content:
                        if key == 'name':
                            el = name
                        content_dict[name][key] = el

                if content_dict[name]['name'] in cf_db:
                    content_dict[name]['value'] = cf_db[content_dict[name]['name']]
                elif content_dict[name]['required']:
                    self.error('Missing %s parameter'%name)

                if 'default' in content_dict[name]:
                    content_dict[name]['value'] = content_dict[name]['default']
                elif name == 'log':
                    if type(content_dict[name]['value']) == str and content_dict[name]['value'] in self.loggers:
                        content_dict[name]['value'] = self.loggers[content_dict[name]['value']]
                    else:
                        self.warning('Wrong logger configuration for database %s'%db_name)
                        content_dict[name]['value'] = self.log

            fct_kwargs  = {x:y['value'] for x,y in content_dict.items()}

            if db_type == 'mysql':
                user,password,host,port,name = cf_db['user'], cf_db['password'], cf_db['host'], cf_db['port'], cf_db['name']
                cnx_str        = 'mysql+pymysql://%s:%s@%s:%s/%s'%(user,password,host,port,name)
            elif db_type == 'oracle':
                user,password,host,port,name = cf_db['user'], cf_db['password'], cf_db['host'], cf_db['port'], cf_db['sid']
                cnx_str        = 'oracle://%s:%s@%s:%s/%s'%(user,password,host,port,name)
            elif db_type == "sqlite":
                cnx_str        = 'sqlite:///' + cf_db['path']

            if cnx_str is not None:
                cf_db['cnx']    = cnx_str
                db_cnx[db_name] = cf_db

        self.db_cnx = db_cnx

        for db_name in self.databases:
            if self.databases[db_name].log is None:
                self.databases[db_name].log = self.log

        # Set logger dabatase
        for logger_name, log in self.loggers.items():
            if log.database_name:
                if not log.database_name in self.databases:
                    self.log.error('Missing database <%s> configuration for logger <%s>'%(log.database_name,logger_name))
                    continue
                log.database = self.databases[log.database_name]

    def get_logger(self,name='main',default_level='INFO') -> AlphaLogger:
        if not 'main' in self.loggers:
            self.loggers['main'] = AlphaLogger(
                name,
                filename    = 'main',
                root        = self.logger_root,
                level       = default_level,
                colors      = self.get("colors/loggers")
            )
        if name not in self.loggers:
            self.warning('%s is not configured as a logger in %s'%(name,self.filepath))
            """log = AlphaLogger(
                name,
                filename    = name,
                root        = self.logger_root,
                level       = default_level,
                colors      = self.get("colors/loggers")
            )"""
            return self.loggers['main']
        return  self.loggers[name] 

    def get(self,path=[],root=True,default=None):
        value       = self.get_parameter_path(path)
        if value is None and root:
            value   = self.get_value_from_main_config(path)
        return value if value is not None else default

    def get_path(self,parameters):
        if type(parameters) == str and '/' in parameters:
            parameters = parameters.split('/')
        if type(parameters) == str:
            parameters = [parameters]
        return parameters

    def get_parameter_path(self,parameters,data=None,level=1):
        parameters = self.get_path(parameters)
        if parameters == '':
            return self.data

        if data is None:
            data = self.data

        if parameters[0] not in data and parameters[0] not in self.data_origin:
            return None
        if len(parameters) == 1:
            if parameters[0] in data:
                return data[parameters[0]]
            if parameters[0] in self.data_origin:
                return self.data_origin[parameters[0]]

        return self.get_parameter_path(parameters[1:],data[parameters[0]],level = level + 1)

    def get_database(self,name):
        if name in self.databases:
            return self.databases[name]
        return None

    def get_value_from_main_config(self,parameter,force_exit=False):
        value = None
        if self.origin is not None:
            value = self.origin.get(parameter)
            if value is not None:
                return value 

        if self.name != 'config':
            if self.origin is not None:
                value = self.origin.get(parameter)
                if value is not None:
                    return value   
        if force_exit:
            self.error('No value is specified for <%s> in %s'%(parameter,self.filepath))
            exit()
        return value            

    def replace_parameters(self,config):
        """Replace parameters formatted has {{<parameter>}} by their values in a json dict
        
        Arguments:
            config {dict} -- json dict to analyse and replace parameters formatted has {{<parameter>}}
        
        Returns:
            dict -- the input dict with parameters replace by their values
        """

        parameters_name, paths = get_parameters_from_config(config, path=None)
        """
            paths                                    parameters_name
            tests / save_directory                   save_root
            files / google-taxonomy / file_path      sources & file_name
            ips / 62.210.244.105 / web / root        root
            save_root                                root & project_name
            sqllite_path                             root
            web / api_root                           root
        """
        parameters = list(set([x for sublist in parameters_name for x in sublist]))

        parameters_value    = {}
        for parameter in parameters:
            # ([3306, 3308], [['variables'], []])
            if '/' in parameter:
                parameter = parameter.split('/')
            values_paths          = search_it(config, parameter)

            # take the first value if any
            if len(values_paths) != 0 and len(values_paths[0]) != 0:
                values, pths               = values_paths

                index, path_len = 0, None

                lenghts = [len(x) for x in pths]
                indexs  = np.where(lenghts == np.amin(lenghts))[0]
                
                if len(indexs) == 0:
                    value                       = self.get_value_from_main_config(parameter)
                elif len(indexs) == 1:
                    value                       = values[indexs[0]]
                else:
                    self.error('Too many possible value at the same level are specified for parameter <%s>'%parameter)
                    exit()
                
                if isinstance(parameter,list):
                    parameter = '/'.join(parameter)
                parameters_value[parameter] = value
            else:
                if isinstance(parameter,list):
                    parameter = '/'.join(parameter)
                value = self.get_value_from_main_config(parameter,force_exit=True)
                parameters_value[parameter]                       = value

        l = 0
        set_parameter_value(parameters_value,l)

        # Replace parameters values
        set_paths(config,paths,parameters_name,parameters_value,types='parameters')

        # check parameters
        parameters_name, paths = get_parameters_from_config(config, path=None)
        if len(parameters_name) != 0:
            parameters = list(set([x[0] for x in parameters_name if len(x) != 0]))
            for i in range(len(parameters)):
                self.error('Missing parameter "%s" in configuration %s'%(parameters[i],self.filepath))
            if len(parameters) != 0:
                exit()

        self.data = config


def show(config,level=0):
    for key, cf in config.items():
        val = '' if type(cf) == dict else str(cf)
        print('{} {:30} {}'.format('   '*level,key,val))
        if type(cf) == dict:
            show(cf,level + 1)

# config,paths,configs_values,sub_configurations,types='configs'
def set_paths(config,paths,parameters_values,parameters_value,types=None):
    levels = list(set([len(x) for x in paths]))

    for level in levels:
        for i in range(len(parameters_values)):
            if len(paths[i]) == level:
                set_path(config, paths[i], parameters_values[i], parameters_value,types)

def set_path(config,path,parameters,parameters_values,types=None):
    if len(path) == 1:
        if types == 'parameters':
            value   = config[path[0]]
            for parameter in parameters:
                if parameter in parameters_values:
                    parameter_value     = parameters_values[parameter]
                    if value == PAREMETER_PATTERN%parameter:
                        value           = parameter_value
                    elif PAREMETER_PATTERN%parameter in str(value):
                        value           = value.replace(PAREMETER_PATTERN%parameter,str(parameter_value))
                
            config[path[0]]         = value

        elif types == 'configs':
            matchs = get_configs_matchs(config[path[0]])
            if len(matchs) != 0 and matchs[0] in parameters_values:
                sub_configuration       = parameters_values[matchs[0]]
                replacement_data        = {x:y for x,y in sub_configuration.data.items() if x not in sub_configuration.tmp}
                config[path[0]]         = replacement_data
            
        return

    sub_config  = config[path[0]]
    path        = path[1:]

    set_path(sub_config,path,parameters,parameters_values,types)

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
        next_path   = copy.copy(path)
        next_path.append(key)

        if isinstance(target,list) and len(target) == 1:
            target = target[0]
        
        if isinstance(target,list):
            if key == target[0]:
                f, p = search_it(value, target[1:],next_path)
                found.extend(f)
                paths.extend(p)
        else:
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

def get_configs_matchs(string):
    return re.findall(r"\$config\(([^\$]+)\)",string)

def check_value(value,found,paths,object_type,next_path):
    parameters      = utils.get_parameters(value)

    if object_type == 'parameters':
        results     = [ x.replace('{{','').replace('}}','') for x in parameters]
    else:
        results     = get_configs_matchs(value)

    if len(results) != 0:
        found.append( results)
        paths.append(next_path)

def get_object_from_config(nested,path=None,object_type='parameters'):
    found, paths = [], []
    if path is None:
        path = []

    if isinstance(nested, dict):
        for key, value in nested.items():
            next_path   = copy.copy(path)
            next_path.append(key)

            if isinstance(value, str):
                check_value(value,found,paths,object_type,next_path)
            elif isinstance(value, dict):
                f, p = get_object_from_config(value, next_path,object_type)
                found.extend(f)
                paths.extend(p)
            elif isinstance(value, list):
                f, p = get_object_from_config(value, next_path,object_type)
                found.extend(f)
                paths.extend(p)
    elif isinstance(nested, list):
        for i, value in enumerate(nested):
            next_path   = copy.copy(path)
            next_path.append(i)

            if isinstance(value, str):
                check_value(value,found,paths,object_type,next_path)
            elif isinstance(value, dict):
                f, p = get_object_from_config(value, next_path,object_type)
                found.extend(f)
                paths.extend(p)
            elif isinstance(value, list):
                f, p = get_object_from_config(value, next_path,object_type)
                found.extend(f)
                paths.extend(p)
    return found, paths

def get_parameters_from_config(nested, path=None):
    return get_object_from_config(nested,path=path,object_type='parameters')

def get_configs_from_config(nested, path=None):
    return get_object_from_config(nested,path=path,object_type='configs')

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
        next_path   = copy.copy(path)
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

LIMIT = 100
def set_parameter_value(parameters_value,l):
    if l > 10: 
        print('ERROR: replacement limit exceed for parameter %s'%parameters_value)
        exit()
    l += 1

    replaced    = False
    keys        = list(parameters_value.keys())
    for key, value in parameters_value.items():
        for k in keys:
            if "{{%s}}"%k in str(value) and "{{%s}}"%k != value:
                i = 0
                value       = replace_parameter(k,value,parameters_value[k],i)
                replaced    = True
        parameters_value[key] = value

    if replaced:
        set_parameter_value(parameters_value,l)

def replace_parameter(key,value,replace_value,i):
    if i > LIMIT: 
        print('ERROR: replacement limit exceed for parameter %s'%key)
        exit()
    i += 1

    if isinstance(value,dict):
        replacements = {}
        for k, v in value.items():
            vr = replace_parameter(key,v,replace_value,i)
            if v != vr:
                replacements[k] = vr
        for k, newv in replacements.items():
            value[k] = newv
    elif isinstance(value,list):
        replacements = {}
        i = 0
        for v in value:
            vr = replace_parameter(key,v,replace_value,i)
            if v != vr:
                replacements[i] = vr
            i += 1
        for i, newv in replacements.items():
            value[i] = newv
    else:
        if "{{%s}}"%key == value:
            value   = replace_value
        elif "{{%s}}"%key in str(value):
            value       = value.replace("{{%s}}"%key,replace_value)
    return value