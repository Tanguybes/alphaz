import os, datetime, inspect, sys, re, traceback, uuid, time
import logging
from logging.handlers import TimedRotatingFileHandler
from alphaz.libs import io_lib

import platform 
PLATFORM = platform.system().lower()

from . import _colorations, _utils

if PLATFORM == "windows":
    from concurrent_log_handler import ConcurrentRotatingFileHandler

PROCESSES = {}

class AlphaLogger():   
    date_format             = "%Y-%m-%d %H:%M:%S"
    format_log              = "{$date} - {$level:6} - {$pid:5} - {$file:>20}.{$line:<4} - {$name:<10}: $message" # %(processName)s %(filename)s:%(lineno)s

    monitoring_logger = None

    def __init__(self,name,filename=None,root=None,cmd_output=True,level='INFO',colors=None,database=None):
        self.level          = 'info'
        self.date_str       = ""
        self.database_name  = database
        self.database       = None

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

        self.level_show = _utils.get_level(level if level is not None else 'INFO')
        self.logger.setLevel(self.level_show)

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
    
    def _log(self,message:str,caller,level:str='info',monitor:str=None,save=False,ex:Exception=None):
        """
                frame       = inspect.stack()[1]
        module      = inspect.getmodule(frame[0])
        origin      = "Unknowned"
        if module is not None:
            origin  = os.path.basename(module.__file__)
        """
        if monitor: save = True

        if isinstance(message, Exception):
            text    = traceback.format_exc()

        if monitor is not None and self.monitoring_logger is None:
            self.monitoring_logger  = AlphaMonitorLogger('monitoring',root=self.root,cmd_output=False)

        self.set_current_date()
        self.level                  = level.upper()

        full_message                = self.get_formatted_message(message,caller)

        if ex is not None:
            text            = traceback.format_exc()
            full_message    += "/n" + text

        fct = getattr(self.logger,self.level.lower())
        fct(full_message)
        if monitor is not None:
            fct_monitor = getattr(self.monitoring_logger,self.level.lower())
            fct_monitor(message=full_message.replace(message,"[%s] %s"%(monitor,message)))

        """if save:
            self.__log_in_db(text, origin=origin, type="error")"""

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

        msg = msg.format(*parameters_values).replace(structure%'message',str(message))

        return msg

    def info(self,message,monitor=None,level=1,save=False,ex:Exception=None):
        self._log(message,inspect.getframeinfo(inspect.stack()[level][0]),'info',monitor=monitor,save=save,ex=ex)

    def warning(self,message,monitor=None,level=1,save=False,ex:Exception=None):
        self._log(message,inspect.getframeinfo(inspect.stack()[level][0]),'warning',monitor=monitor,save=save,ex=ex)

    def error(self,message,monitor=None,level=1,save=False,ex:Exception=None):
        self._log(message,inspect.getframeinfo(inspect.stack()[level][0]),'error',monitor=monitor,save=save,ex=ex)

    def debug(self,message,monitor=None,level=1,save=False,ex:Exception=None):
        self._log(message,inspect.getframeinfo(inspect.stack()[level][0]),'debug',monitor=monitor,save=save,ex=ex)

    def critical(self,message, monitor=None,level=1,save=False,ex:Exception=None):
        self._log(message,inspect.getframeinfo(inspect.stack()[level][0]),'critical',monitor=monitor,save=save,ex=ex)

    def set_current_date(self):
        current_date        = datetime.datetime.now()
        self.date_str       = current_date.strftime(self.date_format)

    def process_start(self,name,parameters):
        uuid_process                    = str(uuid.uuid4())
        PROCESSES[uuid_process]    =  {'uuid':uuid,'name':name, 'parameters':parameters,'datetime':datetime.datetime.now()}
        self.process_log(uuid_process, name, parameters, 'START')
        return uuid_process

    def process_end(self, uuid_process, name, parameters, error=None):
        PROCESS_INFOS                   = None
        if uuid_process in PROCESSES:
            PROCESS_INFOS               = PROCESSES[uuid_process] 

        status = 'INFOS'
        if PROCESS_INFOS is not None:
            if name != PROCESS_INFOS['name']:
                status      = 'NAME'
            elif parameters != PROCESS_INFOS['parameters']:
                status      = 'PARAM'
            name        = PROCESS_INFOS['name']
            parameters  = PROCESS_INFOS['parameters']
            status      = 'END'

        if error is not None:
            status = str(error)

        if uuid_process is not None:
            self.process_log(uuid_process, name, parameters, status)

    def trace_show(self):
        traceback.print_exc()

    def __log_in_db(self, message, origin="unspecified", type_="unspecified"):
        from ...models.database.main_definitions import Logs

        # Connect to db
        stackraw    = traceback.format_stack()
        stack       = ''.join(stackraw) if stackraw is not None else ''

        self.database.insert(Logs, values={
            Logs.type_:type_, Logs.origin:origin, Logs.message:message, Logs.stack:stack})

    def print_error(self, error_msg, raise_exception=True):
        '''Display the last error catched'''
        if (str(error_msg)[:3] == '-W-'):
            print('#-# WARNING #-#: ' + str(error_msg)[3:])
        else:
            error_msg = '#-# ERROR #-#: ' + str(error_msg)
            error_msg += ' -----> ' + str(sys.exc_info()[0])
            self.error(error_msg)
            if raise_exception == True:
                raise Exception(0,'#-# ERROR #-#')

    def process_log(self, uuid_process, name, parameters, status):
        from ...models.database.main_definitions import Processes

        if type(parameters) != str:
            parameters = ';'.join([str(x) for x in parameters])

        self.database.insert(Processes, values={
            Processes.uuid:uuid_process, Processes.name:name, Processes.parameters:parameters, Processes.status:status})

class AlphaMonitorLogger(AlphaLogger):
    format_log              = "$message"

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
