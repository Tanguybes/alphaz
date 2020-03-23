import os, datetime, inspect
import logging
from logging.handlers import TimedRotatingFileHandler

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

"""
import subprocess, os, psutil, logging
from logging.handlers import TimedRotatingFileHandler

log_file    = '/home/truegolliath/logs/ensure_golliath.log'
logger      = logging.getLogger('EnsureGolliath')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

log_handler = TimedRotatingFileHandler(
    log_file, when='midnight', backupCount=30
)
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
"""

class AlphaLogger():
    cmd_output  = False
    pid         = None
    level       = 'info'
    date_format = "%Y-%m-%d %H:%M:%S"
    date_str    = ""
    format_log  = "$(date) - $(level) - $(pid) - $(name): $(message)"

    def __init__(self,name,filename=None,root=None,cmd_output=True,level='INFO'):
        if filename is None:
            filename = name
        if root is None:
            """stack       = inspect.stack()
            parentframe = stack[1]
            module      = inspect.getmodule(parentframe[0])
            root        = os.path.abspath(module.__file__).replace(module.__file__,'')"""

            root        = get_alpha_logs_root()

        root            = check_root(root)
        logname         = root + os.sep + filename + '.log'

        # Create logger
        self.logger = logging.getLogger(name)

        self.set_level(level)

        # File handler
        handler         = TimedRotatingFileHandler(logname, when="midnight", interval=1,backupCount=7)
        #handler.suffix  = "%Y%m%d"

        self.logger.addHandler(handler)

        self.pid        = os.getpid()
        self.name       = name
        self.cmd_output = cmd_output
    
    def set_level(self,level):
        self.level_show = level
        lvl = logging.INFO 
        if level.upper() == 'ERROR':
            lvl = logging.ERROR 
        elif level.upper() == 'DEBUG':
            lvl = logging.DEBUG 
        elif level.upper() == 'WARNING':
            lvl = logging.WARNING 
        self.logger.setLevel(lvl)

    def _log(self,message,level='info'):
        self.set_current_date()
        self.level      = level.upper()
        
        message         = self.get_formatted_message(message)

        if self.level == 'INFO':
            self.logger.info(message)
        elif self.level == 'WARNING':
            self.logger.warning(message)
        elif self.level == 'ERROR':
            self.logger.error(message)
        elif self.level == 'DEBUG':
            self.logger.debug(message)

    def get_formatted_message(self,message):
        msg = self.format_log
        
        structure = '$(%s)'
        keys = {
            'date':     self.date_str,
            'pid':      self.pid,
            'level':    self.level,
            'name':     self.name
        }
        
        for key, value in keys.items():
            if structure%key in self.format_log:
                msg = msg.replace(structure%key,str(value))

        msg = msg.replace(structure%'message',str(message))
        return msg

    def info(self,message):
        self._log(message,'info')

    def warning(self,message):
        self._log(message,'warning')

    def error(self,message):
        self._log(message,'error')

    def debug(self,message):
        self._log(message,'debug')

    def set_current_date(self):
        current_date        = datetime.datetime.now()
        self.date_str       = current_date.strftime(self.date_format)