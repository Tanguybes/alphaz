import os, sys
from ...utils.logger import AlphaLogger
from ...config.config import AlphaConfig

class AlphaCore: 
    root: str               = None
    initiated: bool         = False
    loggers: {AlphaLogger}  = {}
    log: AlphaLogger        = None

    instance                = None

    def __init__(self,file:str):   
        root                = self.get_relative_path(file, level=0)

        self.config         = AlphaConfig('config',root=root)

        logs_directory      = self.config.get("log_directory")
        loggers_config      = self.config.get("loggers")

        print('   INITIATE',logs_directory,loggers_config)

        self.loggers        = self.config.loggers

    def get_relative_path(self, file: str, level = 0, add_to_path=True):
        if level == 0:
            root                    = os.path.dirname(file)
        else:
            root                    = os.sep.join(os.path.dirname(file).split(os.sep)[:-level])
        self.root     = root
        if add_to_path:
            sys.path.append(root)
        return root

    def get_logger(self,*args, **kwargs):
        return self.config.get_logger(*args,**kwargs)

    def get_database(self,*args, **kwargs):
        return self.config.get_database(*args,**kwargs)