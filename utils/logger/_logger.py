import os, datetime, inspect, sys, re
import logging
from logging.handlers import TimedRotatingFileHandler
from alphaz.models.main import singleton
from alphaz.libs import io_lib

import platform 
PLATFORM = platform.system().lower()

from . import _colorations, _utils

if PLATFORM == "windows":
    from concurrent_log_handler import ConcurrentRotatingFileHandler

class AlphaLogger():   
    date_format             = "%Y-%m-%d %H:%M:%S"
    format_log              = "{$date} - {$level:6} - {$pid:5} - {$file:>20}.{$line:<4} - {$name:<10}: $message" # %(processName)s %(filename)s:%(lineno)s

    monitoring_logger = None

    def __init__(self,name,filename=None,root=None,cmd_output=True,level='INFO',colors=None):
        self.level          = 'info'
        self.date_str       = ""

        if filename is None:
            filename        = name
        if root is None:
            """
            parentframe     = inspect.stack()[1]
            module          = inspect.getmodule(parentframe[0])
            root            = os.path.abspath(module.__file__).replace(module.__file__,'')"""
            root            = _utils.get_alpha_logs_root()

        self.root           =  _utils.check_root(root)
        log_path            = self.root + os.sep + filename + '.log'

        # Create logger
        self.logger             = logging.getLogger(name)

        self.set_level(level)

        # File handler
        handler             = TimedRotatingFileHandler(log_path, when="midnight", interval=1,backupCount=7)

        if PLATFORM == "windows":
            handler         = ConcurrentRotatingFileHandler(log_path,"a", 512*1024, 5)
        #handler.suffix  = "%Y%m%d"

        self.logger.addHandler(handler)

        if cmd_output:
            handler = logging.StreamHandler(sys.stdout)
            if colors:
                handler.addFilter(_colorations.ColorFilter(colors))
            self.logger.addHandler(handler)

        self.pid            = os.getpid()
        self.name           = name
        #self.cmd_output     = cmd_output if cmd_output is not None else True
    
    def set_level(self,level):
        self.level_show = _utils.get_level(level)
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

    def get_formatted_message(self,message,caller):
        msg = self.format_log

        parameters = re.findall("\{\$([a-zA-Z0-9]*):?[0-9<>]*\}", msg)

        parameters_values = []

        structure = '$%s'
        keys = {
            'date':     self.date_str,
            'pid':      self.pid,
            'level':    self.level,
            'name':     self.name,
            'path':     caller.filename,
            'file':     caller.filename.split(os.sep)[-1].replace('.py',''),
            'line':     caller.lineno
        }
        
        for parameter_name in parameters:
            if parameter_name in keys:
                msg = msg.replace(structure%parameter_name,'')
                parameters_values.append(keys[parameter_name])

        msg = msg.replace(structure%'message',str(message))

        msg = msg.format(*parameters_values)
        return msg

    def info(self,message,monitor=None,level=1):
        self._log(message,inspect.getframeinfo(inspect.stack()[level][0]),'info',monitor=monitor)

    def warning(self,message,monitor=None,level=1):
        self._log(message,inspect.getframeinfo(inspect.stack()[level][0]),'warning',monitor=monitor)

    def error(self,message,monitor=None,level=1):
        self._log(message,inspect.getframeinfo(inspect.stack()[level][0]),'error',monitor=monitor)

    def debug(self,message,monitor=None,level=1):
        self._log(message,inspect.getframeinfo(inspect.stack()[level][0]),'debug',monitor=monitor)

    def critical(self,message, monitor=None,level=1):
        self._log(message,inspect.getframeinfo(inspect.stack()[level][0]),'critical',monitor=monitor)

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
