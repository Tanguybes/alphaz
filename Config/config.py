
import configparser, os, json, inspect

from ..Libs import converter_lib
from ..Utils.logger import AlphaLogger

def get_alpha_logs_root():
    current_folder  = os.path.dirname(os.path.realpath(__file__))
    dirs            = current_folder.split(os.sep)
    log_dir         = os.sep.join(dirs[:-1]) + os.sep + 'logs'
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)
    return log_dir

class AlphaConfig():
    filename    = None
    exist       = False
    data        = {}

    def __init__(self,name,root=None,filename=None,logger=None):
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

        self.config_file = root + os.sep + self.filename+'.json'

        if not os.path.isfile(self.config_file):
            self.log.error('Config file %s does not exist !'%self.config_file)
            return

        self.exist = True

        self.load()

    def load(self):
        with open(self.config_file) as json_data_file:
            self.data = json.load(json_data_file)

    def isParameterPath(self,parameters,data=None):
        if data is None:
            data = self.data
        if len(parameters) == 0:
            return True
        if parameters[0] not in data:
            return False
        return self.isParameterPath(parameters[1:],data[parameters[0]])

    def getParameterPath(self,parameters,data=None):
        if data is None:
            data = self.data
        if parameters[0] not in data:
            return None
        if len(parameters) == 1:
            return data[parameters[0]]
        return self.getParameterPath(parameters[1:],data[parameters[0]])


        