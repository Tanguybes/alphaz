
import  os, json, inspect, copy, sys, socket, re, platform, getpass
import numpy as np
from typing import List, Dict

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from ._utils import *

from ..main import AlphaClass
from ..main._exception import EXCEPTIONS
from ..logger import AlphaLogger

from ...libs import converter_lib, sql_lib, io_lib

class AlphaConfig(AlphaClass):
    __reserved    =  ['user','configuration','project','ip','platform']

    def __init__(self,
            name: str = 'config',
            filepath: str = None,
            root: str = None,
            filename: str = None,
            log: AlphaLogger = None,
            configuration: str = None,
            logger_root: str = None,
            data: dict = None,
            origin = None,
            core = None,
            core_configuration = None,
            reserved: List[str] = [],
            required: List[str] = []
            ):
        if hasattr(self, 'tmp'): return

        self.reserved = list(set(reserved).union(set(self.__reserved)))
        self.required = required

        name, filepath, root, filename = ensure_filepath(name, filepath, root, filename)

        self.name = name
        self.filepath = filepath
        self.root = root
        self.filename = filename
        self.configuration: str = configuration
        self.logger_root = logger_root
        self.origin = origin
        self.sub_configurations = {}
        self.core = core

        super().__init__(log=log)

        self.tmp         = {}

        self.data_tmp    = {}
        self.data_origin = data if data is not None else {}
        self.data        = data if data is not None else {}

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

        self.core_configuration = core_configuration

        if data is None:
            self._load_raw()

        if data is None and configuration is not None:
            self.set_configuration(configuration)
        else:
            self._load()

    def _load_raw(self):
        if not self.loaded:
            with open(self.filepath, encoding='utf-8') as json_data_file:
                try:
                    self.data_origin = json.load(json_data_file)
                except Exception as ex:
                    print('Configuration file %s is invalid: %s'%(self.filepath, ex))
                    exit()
                self.loaded = True

    def set_configuration(self, configuration, force = False):
        if CONFIGURATIONS.is_configured(self) and not force:
            return

        if configuration is None and self.configuration is None:
            self.error('Configuration need to be explicitely specified in configuration call or config file for %s file'%self.filepath)
            return
        elif configuration is None and self.configuration is not None:
            configuration = self.configuration
            
        self._clean()

        self.configuration = configuration

        self._load()

    def _clean(self):
        # remove tmp from data_origin
        if len(self.tmp) != 0:
            self.data_origin = {x:y for x, y in self.data_origin.items() if x not in self.tmp}

    def _load(self):
        self._check_reserved()
        
        self._set_tmps()

        self._set_configuration()

        self.core_configuration = self.get('core_configuration', root=False) if self.core_configuration is None else self.core_configuration

        # check if loaded
        if not CONFIGURATIONS.load_configuration(self) or not self.core_configuration:
            if self.core_configuration:
                self.info('Reload configuration: %s'%self.filepath)
            self._process_tmps()
            self._init_data()
            self._configure_sub_configurations()
            CONFIGURATIONS.save_configuration(self)
        else:
            self._configure_sub_configurations()

        if self.core_configuration:
            self._check_required()
            self._configure()

    """def set_data(self,value,paths=[]):
        ensure_path(self.data_origin,paths,value=value)"""

    def _set_configuration(self):
        if "configurations" in self.data_origin:
            configurations = self.data_origin["configurations"]
            
            default_configuration = None
            if "default_configuration" in self.data_origin:
                default_configuration = self.data_origin['default_configuration']

            if self.configuration is not None and self.configuration in configurations:
                self.data_tmp['configurations'] = configurations[self.configuration]
            elif default_configuration is not None and default_configuration in configurations:
                self.data_tmp['configurations'] = configurations[default_configuration]
                self.configuration = default_configuration
        self._add_tmp('configuration', self.configuration)

    def _init_data(self):
        config          = copy.deepcopy(self.data_origin)
        for key, values in self.data_tmp.items():
            merge_configuration(config, values, replace=True)
            del config[key]

        self.data = self._replace_parameters(config)

    def _configure(self):
        # Paths
        if self.is_path("paths"):
            for path in self.get("paths"):
                sys.path.append(path)

        if self.is_path("envs"):
            for env, value in self.get("envs").items():
                os.environ[env] = value

        self._set_loggers()
        self._configure_databases()

        if self.core_configuration: 
            sequence = ', '.join(["%s=<%s>%s"%(tmp, tmp_value, '*' if tmp+'s' in self.data_tmp else '') for tmp, tmp_value in self.tmp.items() ])
            self.info('Configuration %s initiated for: %s'%(self.filepath.split(os.sep)[-1],sequence))

        # SET ENVIRONMENT VARIABLES
        if self.core is not None:
            set_environment_variables(self.get('environment'))

        #loggers_config      = self.config.get("loggers")

            self.core.loggers        = self.loggers
            self.core.log            = self.get_logger('main')

            exceptions              = self.get('exceptions')
            if exceptions is not None:
                for exception_group in exceptions:
                    for exception_name, exception_configuration in exception_group.items():
                        if not exception_name in EXCEPTIONS:
                            EXCEPTIONS[exception_name] = exception_configuration
                        else:
                            self.log.error('Duplicate exception name for %s'%exception_name)

    def _configure_sub_configurations(self):
        if not self.core_configuration:
            return 

        config = self.data
        # get sub configurations
        self.sub_configurations = {}
        configs_values, paths = get_configs_from_config(config, path=None)

        for i, values in enumerate(configs_values):
            config_path = values[0]
            if not config_path in self.sub_configurations:
                name                            = config_path.split(os.sep)[-1]

                self.sub_configurations[config_path] = AlphaConfig(name=name,filepath=config_path,
                    log=self.log,
                    logger_root=self.logger_root,
                    origin=self,
                    configuration = self.configuration
                )

        # replace sub configurations
        set_configs_paths(config, paths, configs_values,self.sub_configurations)
        self.data = config

    def get_config(self,path=[],configuration=None):
        path = self._get_path(path)
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

    def _set_loggers(self):
        if not self.core_configuration:
            return

        # loggers
        self.logger_root = self.get("directories/logs")
        if self.logger_root is None:
            self.error('Missing "directories/logs" entry in configuration file %s'%self.filepath)
            exit()

        # log
        
        colors = self.get("colors/loggers/rules") if self.get("colors/loggers/active") else None
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
                        cmd_output  = logger_config.get("cmd_output", default=True),
                        level       = logger_config.get("level"),
                        colors      = colors,
                        database    = logger_config.get("database"),
                        excludes    = logger_config.get('excludes')
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

    def _replace_parameters(self,config):
        """Replace parameters formatted has {{<parameter>}} by their values in
        a json dict.

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
                    value                       = self.get(parameter)
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
                value = self.get(parameter, force_exit=True)
                parameters_value[parameter]                       = value

        l = 0
        set_parameter_value(parameters_value,l)

        # Replace parameters values
        set_paths(config,paths,parameters_name,parameters_value)

        # check parameters
        parameters_name, paths = get_parameters_from_config(config, path=None)
        if len(parameters_name) != 0:
            parameters = list(set([x[0] for x in parameters_name if len(x) != 0]))
            for i in range(len(parameters)):
                self.error('Missing parameter "%s" in configuration %s'%(parameters[i],self.filepath))
            if len(parameters) != 0:
                exit()
        return config

    def get_logger(self,name='main',default_level='INFO') -> AlphaLogger:
        colors = self.get("colors/loggers/rules") if self.get("colors/loggers/active") else None
        if not 'main' in self.loggers:
            self.loggers['main'] = AlphaLogger(
                name,
                filename    = 'main',
                root        = self.logger_root,
                level       = default_level,
                colors      = colors
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

    def _get_value_from_main_config(self,parameter,force_exit=False):
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
            self.error('No value is specified for <%s> in %s'%(parameter, self.filepath))
            exit()
        return value

    def get(self,path=[],root:bool=True,default=None,force_exit:bool=False,configuration:str=None,type_=None):
        value       = self._get_parameter_path(path)
        if value is None and root:
            value   = self._get_value_from_main_config(path,force_exit=force_exit)
        if type_ is not None:
            try:
                value = type_(value)
            except Exception as ex:
                self.error("Cannot convert parameter <%s> to type <%s> for value <%s>"%(path, type_,value),ex=ex)
        if value is None:
            return default
        return value

    def _get_parameter_path(self,parameters,data=None,level=1):
        parameters = self._get_path(parameters)
        if parameters == '':
            return self.data

        if data is None:
            data = self.data

        not_init = parameters[0] not in self.data_origin and parameters[0] not in self.tmp

        if parameters[0] not in data and not_init:
            return None

        if len(parameters) == 1:
            if parameters[0] in data:
                return data[parameters[0]]
            if parameters[0] in self.data_origin:
                return self.data_origin[parameters[0]]
            if parameters[0] in self.tmp:
                return self.tmp[parameters[0]]

        return self._get_parameter_path(parameters[1:],data[parameters[0]],level = level + 1)

    def _get_path(self,parameters):
        if type(parameters) == str and '/' in parameters:
            parameters = parameters.split('/')
        if type(parameters) == str:
            parameters = [parameters]
        return parameters

    def _configure_databases(self):
        if not self.is_path('databases'): return

        config = self.get("databases")
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
                c = ""
                user,password,host,port = cf_db['user'], cf_db['password'], cf_db['host'], cf_db['port']
                if "sid" in cf_db:
                    name = cf_db['sid']
                    c = '%s:%s/%s'%(host,port,name)
                elif "service_name" in cf_db:
                    name = cf_db['service_name']
                    c = "(DESCRIPTION = (LOAD_BALANCE=on) (FAILOVER=ON) (ADDRESS = (PROTOCOL = TCP)(HOST = %s)(PORT = %s)) (CONNECT_DATA = (SERVER = DEDICATED) (SERVICE_NAME = %s)))"%(host,port,name)
                cnx_str        = 'oracle://%s:%s@%s'%(user,password,c)
            elif db_type == "sqlite":
                cnx_str        = 'sqlite:///' + cf_db['path']

            if cnx_str is not None:
                cf_db['cnx']    = cnx_str
                db_cnx[db_name] = cf_db

        self.db_cnx = db_cnx

        # TODO: remove self.databases elements ? 
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

    def get_database(self,name):
        if name in self.databases:
            return self.databases[name]
        return None

    def is_parameter_path(self,parameters,data=None):
        if type(parameters) == str and "/" in parameters:
            parameters = parameters.split('/')
        if type(parameters) == str:
            parameters = [parameters]
        if data is None:
            data = self.data
        if len(parameters) == 0:
            return True
        if parameters[0] not in data:
            return False
        return self.is_parameter_path(parameters[1:], data[parameters[0]])

    def is_path(self,parameters,data=None):
        return self.is_parameter_path(parameters,data=data)

    def save(self):
        self.info('Save configuration file at %s'%self.filepath)

        self._clean()

        with open(self.filepath,'w', encoding='utf-8') as json_data_file:
            json.dump(self.data_origin,json_data_file, sort_keys=True, indent=4, ensure_ascii = False)

    def show(self):
        show(self.data)

    def _check_required(self):
        if 'required' in self.data:
            self.required = list(set(self.data['required']).union(set(self.required)))

        for path in self.required:
            if not self.is_path(path):
                self.log.error("Missing '%s' key in config file"%(path))
                self.valid = False
                exit()
        
    def _check_reserved(self):
        for reserved_name in self.reserved:
            if reserved_name in self.data_origin:
                self.error("<%s> entry in configuration %s is reserved"%(reserved_name,self.filepath))
                exit()

    def _add_tmp(self,name,value):
        if name in self.data_origin:
            self.error('<%s> entry in configuration %s is reserved'%(name,self.filepath))
            exit()

        self.tmp[name]          = value
        #self.data_origin[name]  = value # TODO: check

    def get_tmp(self,name):
        if not name in self.tmp: return None
        return self.tmp[name]

    def _set_tmps(self):
        # tmps
        self._add_tmp('project', os.getcwd())

        # USER
        user = getpass.getuser()
        self._add_tmp('user',user)

        current_ip = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
        self._add_tmp('ip',current_ip)

        system_platform    = platform.system().lower()
        self._add_tmp('platform',system_platform)

    def get_key(self,raw=False):
        return self.filepath + ": " + " - ".join("%s=%s"%(x,y) for x,y in self.tmp.items() if not raw or x != 'configuration')

    def _process_tmps(self):
        to_process = ["user","ip","platform"]

        for name in to_process:
            if name + 's' in self.data_origin:
                users = self.data_origin[name + 's']
                if self.get_tmp(name) in users:
                    self.data_tmp[name + 's'] = self.data_origin[name + 's'][self.get_tmp(name)]


def load_raw_sub_configurations(data):
    sub_configurations = {}

    configs_values, paths = get_configs_from_config(data, path=None)
    for i, values in enumerate(configs_values):
        config_path = values[0]
        if not config_path in sub_configurations:
            name                            = config_path.split(os.sep)[-1]

            sub_configurations[config_path] = AlphaConfig(name=name,filepath=config_path)
    return sub_configurations

class AlphaConfigurations(object):
    _name = 'tmp/configs'
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self):
        self._configurations: Dict[str, AlphaConfig] = {}
        if os.path.exists(self._name):
            loaded_configurations = io_lib.unarchive_object(self._name)
            if type(loaded_configurations) == dict:
                for key, values in loaded_configurations.items():
                    if self._is_valid_configuration(values):
                        self._configurations[key] = values

    def _is_valid_configuration(self,configuration):
        valid = False
        if type(configuration) == dict:
            valid = True
            for key, values in configuration.items():
                if type(values) != dict:
                    valid = False
        return valid

    def load_configuration(self, config: AlphaConfig) -> bool:
        path = config.get_key()

        if path in self._configurations:
            loaded_configuration = self._configurations[path]

            if not "sub_configurations" in loaded_configuration or not "data_origin" in loaded_configuration:
                return False

            if loaded_configuration and loaded_configuration["data_origin"] == config.data_origin:
                for key in loaded_configuration:
                    if hasattr(config, key):
                        setattr(config, key, loaded_configuration[key])

                # check sub configurations
                for path, sub_config in loaded_configuration["sub_configurations"].items():
                    if os.path.getsize(path) != sub_config["size"]:
                        print("Need to reload %s"%path)
                        return False
                return True
        return False

    def save_configuration(self, config: AlphaConfig):
        key = config.get_key()
        dataset = {
            'data_origin': config.data_origin,
            'data_tmp': config.data_tmp,
            "data": config.data,
            "sub_configurations": {x.filepath: {"data_origin":x.data_origin,"data_tmp":x.data_tmp,"data":x.data,"size":os.path.getsize(x.filepath)} for x in config.sub_configurations.values()}
        }
        try:
            self._configurations[key] = dataset
        except:
            self._configurations: Dict[str,object] = {key: dataset}
        io_lib.archive_object(self._configurations, self._name)

    def is_configured(self, config) -> bool:
        path = config.get_key()
        return path in self._configurations

CONFIGURATIONS = AlphaConfigurations()
