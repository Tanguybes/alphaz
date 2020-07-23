import os, datetime, inspect
import logging
from logging.handlers import TimedRotatingFileHandler
from alphaz.models.main.singleton import singleton

import platform 
plt = platform.system()

if plt.lower() == "windows":
    from concurrent_log_handler import ConcurrentRotatingFileHandler

def get_alpha_logs_root():
    current_folder  = os.path.dirname(os.path.realpath(__file__))
    dirs            = current_folder.split(os.sep)
    log_dir         = os.sep.join(dirs[:-1]) + os.sep + 'logs'
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)
    return log_dir

def check_root(root):
    if root == '':
        return root
    if root is None:
        root = get_alpha_logs_root()

    if not os.path.isdir(root):
        os.makedirs(root)
    return root

def get_level(level):
    lvl = logging.INFO 
    if level.upper() == 'ERROR':
        lvl = logging.ERROR 
    elif level.upper() == 'DEBUG':
        lvl = logging.DEBUG 
    elif level.upper() == 'WARNING':
        lvl = logging.WARNING 
    return lvl

class AlphaLogger():   
    date_format             = "%Y-%m-%d %H:%M:%S"
    format_log              = "$(date) - $(level) - $(pid) - $(file) - $(line) - $(name): $(message)" # %(processName)s %(filename)s:%(lineno)s

    monitoring_logger = None

    def __init__(self,name,filename=None,root=None,cmd_output=True,level='INFO'):
        self.level          = 'info'
        self.date_str       = ""
        self.cmd_output     = False

        if filename is None:
            filename        = name
        if root is None:
            """
            parentframe     = inspect.stack()[1]
            module          = inspect.getmodule(parentframe[0])
            root            = os.path.abspath(module.__file__).replace(module.__file__,'')"""
            root            = get_alpha_logs_root()

        self.root           = check_root(root)
        log_path            = self.root + os.sep + filename + '.log'

        # Create logger
        self.logger             = logging.getLogger(name)

        self.set_level(level)

        # File handler
        handler             = TimedRotatingFileHandler(log_path, when="midnight", interval=1,backupCount=7)

        if plt.lower() == "windows":
            handler         = ConcurrentRotatingFileHandler(log_path,"a", 512*1024, 5)
        #handler.suffix  = "%Y%m%d"

        self.logger.addHandler(handler)

        self.pid            = os.getpid()
        self.name           = name
        self.cmd_output     = cmd_output if cmd_output is not None else True
    
    def set_level(self,level):
        self.level_show = get_level(level)
        self.logger.setLevel(self.level_show)

    def _log(self,message:str,caller,level:str='info',monitor:str=None):
        if monitor is not None and self.monitoring_logger is None:
            self.monitoring_logger  = AlphaMonitorLogger('monitoring',root=self.root,cmd_output=False)

        self.set_current_date()
        self.level                  = level.upper()
        
        full_message                = self.get_formatted_message(message,caller)

        fct = getattr(self.logger,self.level.lower())
        fct(full_message)
        if monitor is not None:
            fct_monitor = getattr(self.monitoring_logger,self.level.lower())
            fct_monitor(full_message.replace(self.name,monitor))

        if self.cmd_output and get_level(self.level) >= self.level_show:
            print('   ',full_message)

    def get_formatted_message(self,message,caller):
        msg = self.format_log
        
        structure = '$(%s)'
        keys = {
            'date':     self.date_str,
            'pid':      self.pid,
            'level':    self.level,
            'name':     self.name,
            'path':     caller.filename,
            'file':     caller.filename.split(os.sep)[-1].replace('.py',''),
            'line':     caller.lineno
        }
        
        for key, value in keys.items():
            if structure%key in self.format_log:
                msg = msg.replace(structure%key,str(value))

        msg = msg.replace(structure%'message',str(message))
        return msg

    def info(self,message,monitor=None):
        self._log(message,inspect.getframeinfo(inspect.stack()[1][0]),'info',monitor=monitor)

    def warning(self,message,monitor=None):
        self._log(message,inspect.getframeinfo(inspect.stack()[1][0]),'warning',monitor=monitor)

    def error(self,message,monitor=None):
        self._log(message,inspect.getframeinfo(inspect.stack()[1][0]),'error',monitor=monitor)

    def debug(self,message,monitor=None):
        self._log(message,inspect.getframeinfo(inspect.stack()[1][0]),'debug',monitor=monitor)

    def critical(self,message, monitor=None):
        self._log(message,inspect.getframeinfo(inspect.stack()[1][0]),'critical',monitor=monitor)

    def set_current_date(self):
        current_date        = datetime.datetime.now()
        self.date_str       = current_date.strftime(self.date_format)

@singleton
class AlphaMonitorLogger(AlphaLogger):
    format_log              = "$(message)"

"""
@singleton
class AlphaLogManager:
    loggers: {AlphaLogger}  = {}

    def is_logger(self,name):
        return name in self.loggers
    
    def get_logger(self,name):
        if self.is_logger(name):
            return self.loggers[name]
        return None

    def set_logger(self,name,logger):
        self.loggers[name] = logger

log_manager = AlphaLogManager()"""
