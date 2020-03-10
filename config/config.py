
import  os, json, inspect, copy

from ..libs import converter_lib
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

    def __init__(self,name='config',filepath=None,root=None,filename=None,logger=None):
        if filepath is not None:
            if not filepath[-5:] == '.json':
                filepath = filepath + '.json'

            filename    = os.path.basename(filepath).split('.')[0]
            root        = os.path.abspath(filepath).replace('%s.json'%filename,'')
            if name == 'config':
                name    = filename

        if root is None:
            stack       = inspect.stack()
            parentframe = stack[1]
            module      = inspect.getmodule(parentframe[0])
            root        = os.path.abspath(module.__file__).replace(module.__file__,'')
        
        if logger is None:
            logger      = AlphaLogger(type(self).__name__,type(self).__name__.lower(),root=get_alpha_logs_root())
        self.log        = logger

        if filename is None:
            filename = name.lower()
        self.filename = filename

        self.config_file = root + os.sep + self.filename + '.json'

        if not os.path.isfile(self.config_file):
            self.log.error('Config file %s does not exist !'%self.config_file)
            return

        self.exist = True

        self.load()

    def load(self):
        with open(self.config_file) as json_data_file:
            self.data_origin = json.load(json_data_file)

        if "env" in self.data_origin:
            env = self.data_origin["env"]
            if "envs" in self.data_origin and env in self.data_origin["envs"]:
                self.data_env = self.data_origin["envs"][env]

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

    def init_data(self):
        config      = copy.deepcopy(self.data_origin)
        config_env  = copy.deepcopy(self.data_env)
        merge_configuration(config,config_env,replace=True)

        for p,v in config.items():
            print('   {:20} {}'.format(p,str(v)))

        print('    ENV')
        for p,v in config_env.items():
            print('   {:20} {}'.format(p,str(v)))

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


        