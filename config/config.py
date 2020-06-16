
import  os, json, inspect, copy, sys, socket
import numpy as np
from ..libs import converter_lib, sql_lib, io_lib
from ..utils.logger import AlphaLogger, get_alpha_logs_root
from .utils import merge_configuration, get_parameters
from ..models.database.structure import AlphaDatabase

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base




import platform, getpass

system_platform    = platform.system()

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
    name        = None
    root        = None
    log         = None
    filename    = None
    filepath: str = None
    exist       = False
    valid       = True
    configuration = None

    logger_root = None

    data_origin = {}
    data        = {}
    data_env    = {}
    data_user   = {}

    databases   = {}
    loggers     = {}

    infos       = []
    warnings    = []

    db_cnx      = {}

    reserved    =  ['user']

    cnx_str     = None
    api         = None

    def __init__(self,name='config',filepath=None,root=None,filename=None,log=None,configuration=None,logger_root=None,data=None):
        self.name = name
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
            root            = os.path.abspath(module.__file__).replace(module.__file__,'')
        self.root           = root        
        # config file
        if filename is None:
            filename        = name.lower()
        self.filename       = filename
        self.filepath       = root + os.sep + filename + '.json'
        self.config_file    = self.filepath if root.strip() != '' else self.filename + '.json'

        self.log = log
        
        if data is None:
            self.set_configuration(configuration)
        else:
            self.data_origin  = data
            self.data         = data

    def set_configuration(self,configuration):
        self.info('Setting <%s> configuration for file %s'%(configuration,self.config_file))
        
        if os.path.isfile(self.config_file):
            self.exist = True
            self.load(configuration)
            self.check_required()
        else:
            print('Config file %s does not exist !'%self.config_file)
            exit()

    def info(self,message):
        if self.log is not None:
            if len(self.infos) != 0:
                for info in self.infos:
                    self.log.info(info)
                self.infos = []
            self.log.info(message)
        else:
            self.infos.append(message)

    def warning(self,message):
        if self.log is not None:
            if len(self.warnings) != 0:
                for msg in self.warnings:
                    self.log.warning(msg)
                self.warnings = []
            self.log.warning(message)
        else:
            self.warnings.append(message)

    def error(self,message,out=True):
        for info in self.infos:
            print('   INFO: %s'%info)
        if self.log is not None:
            self.log.error(message)
        else:
            print('   ERROR: %s'%message)
        if out: exit()

    def get_config(self,path=[]):
        config_data = self.get(path)

        config      = AlphaConfig(
            name    = self.name,
            root    = self.root,
            log     = self.log,
            configuration   = self.configuration,
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

    def load(self,configuration):
        with open(self.config_file) as json_data_file:
            self.data_origin = json.load(json_data_file)
        
        self.__check_reserved()

        """if "imports" in self.data_origin:
            imports = self.data_origin['imports']
            for filepath in imports:
                if not os.path.isfile(filepath + '.json'):
                    self.error('Cannot import file %s'%(filepath + '.json'))
                    exit()
            data = {}
            with open(filepath + '.json') as json_data_file:
                data[filepath] = json.load(json_data_file)

            exit()"""

        if "configurations" in self.data_origin:
            configurations = self.data_origin["configurations"]
            
            default_configuration = None
            if "configuration" in self.data_origin:
                default_configuration = self.data_origin['configuration']

            if configuration is not None and configuration in configurations:
                self.data_env = configurations[configuration]
            elif default_configuration is not None and default_configuration in configurations:
                self.data_env = configurations[default_configuration]

        self.configuration = configuration

        user = getpass.getuser()
        self.data_origin['user'] = user

        if "users" in self.data_origin:
            users = self.data_origin["users"]
            
            if user in users:
                self.info('User "%s" detected in configuration'%user)
                self.data_user = self.data_origin["users"][user]
            #del self.data_origin["users"]

        current_ip = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]

        if "ips" in self.data_origin:
            ips = self.data_origin["ips"]
            if current_ip in ips:
                self.info('Ip "%s" detected in configuration'%current_ip)
                self.data_user = self.data_origin["ips"][current_ip]

        self.init_data()

        self.info('Configuration initiated')

    def show(self):
        show(self.data)

    def save(self):
        self.info('Save configuration file at %s'%self.config_file)
        del self.data_origin['user']
        with open(self.config_file,'w') as json_data_file:
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

    def init_data(self):
        config      = copy.deepcopy(self.data_origin)
        config_env  = copy.deepcopy(self.data_env)
        config_user = copy.deepcopy(self.data_user)

        merge_configuration(config,config_user,replace=True)

        merge_configuration(config,config_env,replace=True)

        if 'users' in config:
            del config['users']

        debug = False
        if debug:
            print('\n    USER\n')
            for p,v in config_user.items():
                print('   {:20} {}'.format(p,str(v)))

            print('\n    ENV\n')
            for p,v in config_env.items():
                print('   {:20} {}'.format(p,str(v)))

            print('\n    FULL\n')
            for p,v in config.items():
                print('   {:20} {}'.format(p,str(v)))

        self.data = self.replace_parameters(config)

        if "paths" in config:
            for path in config["paths"]:
                sys.path.append(path)

        # loggers
        self.logger_root = config.get("logs_directory")
        if self.logger_root is None:
          self.error('Missing "logs_directory" entry in configuration file %s'%self.config_file)
          exit()
        #if self.logger_root is None:
        #    self.logger_root    = self.root + os.sep + 'logs' if "log_directory" not in config else config.get("log_directory")
        
        # log
        if self.log is None:
            log_filename        = "alpha" #type(self).__name__.lower()
            self.log            = AlphaLogger(type(self).__name__,log_filename,root=self.logger_root)

        if self.is_path("loggers"):
            for logger_name in self.get("loggers").keys():
                logger_config   = self.get_config(["loggers",logger_name])

                root            = logger_config.get("root")

                self.loggers[logger_name] = AlphaLogger(
                    logger_name,
                    filename    = logger_config.get("filename"),
                    root        = root if root is not None else self.logger_root,
                    cmd_output  = logger_config.get("cmd_output"),
                    level       = logger_config.get("level")
                )
            
        main_logger_name = "main"
        if not main_logger_name in self.loggers:
            self.log = AlphaLogger(
                main_logger_name,
                root        = self.logger_root,
                cmd_output  = True
            )
            self.loggers[main_logger_name] = self.log
        """else:
            self.log        = self.loggers[main_logger_name]"""

        if 'databases' in config:
            self.configure_databases(config["databases"])

        #self.show()

    def configure_databases(self,config):
        # Databases
        structure   = {'name':None,'required':False,'value':None}

        db_cnx      = {}
        for db_name, cf_db in config.items():
            self.info('Configurating database %s'%db_name)

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

            new         = "new" in cf_db and cf_db['new']

            if not new:
                self.databases[db_name] = AlphaDatabase(**fct_kwargs)
                if not self.databases[db_name].test():
                    self.error('Cannot connect to "%s":\n\n%s'%(db_name,"\n".join(["%s:%s"%(x,y) for x,y in content_dict.items()]) ) )
                else:
                    self.info('Database connection to "%s" is valid'%db_name)
            else:
                if db_type == 'mysql':
                    user,password,host,port,name = cf_db['user'], cf_db['password'], cf_db['host'], cf_db['port'], cf_db['name']
                    cnx_str        = 'mysql+pymysql://%s:%s@%s:%s/%s'%(user,password,host,port,name)
                elif db_type == "sqlite":
                    cnx_str        = 'sqlite:///' + cf_db['path']

                if cnx_str is not None:
                    cf_db['cnx']    = cnx_str
                    db_cnx[db_name] = cf_db

        self.db_cnx = db_cnx

        for db_name in self.databases:
            if self.databases[db_name].log is None:
                self.databases[db_name].log = self.log

    def get_logger(self,name):
        if name not in self.loggers:
            self.error('%s is not configured as a logger'%name)
            return self.log
        return  self.loggers[name] 

    def get(self,path=[]):

        """if type(path) == str:
            values, paths = search_it(self.data, path, path=None)
            if len(values) != 0:
                nbs     = [len(x) for x in paths]
                index   = np.argmin(nbs)
                return values[index]"""
        return self.get_parameter_path(path)

    def get_parameter_path(self,parameters,data=None,level=1):
        if '/' in parameters:
            parameters = parameters.split('/')
        if parameters == '':
            return self.data
        if type(parameters) == str:
            parameters = [parameters]

        #print('%s%s'%('   '*level,' > '.join(parameters)))

        if data is None:
            data = self.data

        if parameters[0] not in data:
            return None
        if len(parameters) == 1:
            #print('%s%s: %s'%('   '*level,' > '.join(parameters),data[parameters[0]]))
            return data[parameters[0]]

        return self.get_parameter_path(parameters[1:],data[parameters[0]],level = level + 1)

    def get_database(self,name):
        if name in self.databases:
            return self.databases[name]
        return None

    def replace_parameters(self,config):
        """Replace parameters formatted has {{<parameter>}} by their values in a json dict
        
        Arguments:
            config {dict} -- json dict to analyse and replace parameters formatted has {{<parameter>}}
        
        Returns:
            dict -- the input dict with parameters replace by their values
        """

        parameters_values, paths = get_parameters_from_config(config, path=None)
        """
            tests / save_directory                   save_root
            menus / save_directory                   save_root
            files / google-taxonomy / file_path      sources & file_name
            ips / 62.210.244.105 / web / root        root
            ips / 62.210.244.105 / web / api_root    root
            save_root                                root & project_name
            logs_directory                           root & project_name
            sqllite_path                             root
            web / root                               root
            web / api_root                           root
        """

        """print('\nParameters:')
        for i in range(len(parameters_values)):
            print('     {:40} {}'.format(' / '.join(paths[i]),' & '.join(parameters_values[i])))"""

        parameters = []
        for i in range(len(parameters_values)):
            parameters.extend(parameters_values[i])

        parameters          = list(set(parameters))
        parameters_value    = {}
        for parameter in parameters:
            # ([3306, 3308], [['variables'], []])
            if '/' in parameter:
                parameter = parameter.split('/')
            values_paths          = search_it(config,parameter)

            # take the first value if any
            if len(values_paths) != 0 and len(values_paths[0]) != 0:
                values, pths               = values_paths

                index, path_len = 0, None

                lenghts = [len(x) for x in pths]
                indexs = np.where(lenghts == np.amin(lenghts))[0]
                if len(indexs) == 0:
                    self.error('No value is specified for %s'%parameter)
                    exit()
                elif len(indexs) == 1:
                    index = indexs[0]
                else:
                    self.error('Too many possible value at the same level are specified for parameter <%s>'%parameter)
                    exit()
                
                value                       = values[index]
                if isinstance(parameter,list):
                    parameter = '/'.join(parameter)
                parameters_value[parameter] = convert_value(value)
            else:
                self.error('No value is specified for %s'%parameter)
                exit()

        """l = 0
        for key, value in parameters_value.items():
            print(key,value)"""

        l = 0
        set_parameter_value(parameters_value,l)

        levels = list(set([len(x) for x in paths]))

        for level in levels:
            for i in range(len(parameters_values)):
                if len(paths[i]) == level:
                    set_path(config, paths[i], parameters_values[i], parameters_value)

        # check parameters
        parameters_values, paths = get_parameters_from_config(config, path=None)
        if len(parameters_values) != 0:
            parameters = list(set([x[0] for x in parameters_values]))
            for i in range(len(parameters)):
                self.error('Missing parameter "%s" in configuration %s'%(parameters[i],self.filepath))
            exit()

        return config

def show(config,level=0):
    for key, cf in config.items():
        val = '' if type(cf) == dict else str(cf)
        print('{} {:30} {}'.format('   '*level,key,val))
        if type(cf) == dict:
            show(cf,level + 1)

def set_path(config,path,parameters,parameters_values):
    if len(path) == 1:
        value   = convert_value(config[path[0]])
        for parameter in parameters:
            #print(parameter,parameters_values)
            if parameter in parameters_values:
                parameter_value = convert_value(parameters_values[parameter])
                if value == PAREMETER_PATTERN%parameter:
                    value = parameter_value
                elif PAREMETER_PATTERN%parameter in str(value):
                    value = value.replace(PAREMETER_PATTERN%parameter,str(parameter_value))
        config[path[0]]         = value
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
        value       = convert_value(value)
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

def get_parameters_from_config(nested, path=None):
    found, paths = [], []
    if path is None:
        path = []

    for key, value in nested.items():
        value       = convert_value(value)
        next_path   = copy.copy(path)
        next_path.append(key)

        if isinstance(value, str):
            parameters = get_parameters(value)
            if len(parameters) != 0:
                found.append([ x.replace('{{','').replace('}}','') for x in parameters])
                paths.append(next_path)
        elif isinstance(value, dict):
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
        value       = convert_value(value)
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

def convert_value(value):
    systems = ['windows', 'unix']
    if type(value) == dict and system_platform.lower() in systems:
        if system_platform.lower() in value:
            value = value[system_platform.lower()]
    return value