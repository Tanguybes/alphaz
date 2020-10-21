import os, sys, datetime, glob, importlib, inspect

from ....utils.logger import AlphaLogger
from ....config.config import AlphaConfig
from ....libs import io_lib, flask_lib, database_lib
from ....models import database as database_models
from ....models.main._exception import EXCEPTIONS

from ...api import AlphaFlask
from ...database.structure import AlphaDatabase

from . import _utils

import alphaz

class AlphaCore: 
    instance    = None

    def __init__(self,file:str): 
        self.root:str               = self.get_relative_path(file, level=0)
        self.config                 = None
        self.log: AlphaLogger       = None
        self.loggers: {AlphaLogger} = {}
        self.initiated: bool        = False
        self.databases: dict        = {}
        self.configuration: str     = None
        self.configuration_name: str = None
        self.ma                     = None
        self.db                     = None
        self.api                    = None
        
        if 'ALPHA_CONF' in os.environ:
            self.set_configuration(os.environ['ALPHA_CONF'])

    def set_configuration(self,configuration_name):
        if self.config is not None: return

        self.config         = AlphaConfig('config',root=self.root,configuration=configuration_name)
        self.config.set_configuration(configuration_name)
        self.configuration  = self.config.configuration
        self.configuration_name = configuration_name

        # SET ENVIRONMENT VARIABLES
        _utils.set_environment_variables(self.config.get('environment'))

        loggers_config      = self.config.get("loggers")

        self.loggers        = self.config.loggers

        self.log            = self.config.get_logger('main')

        exceptions          = self.config.get('exceptions')
        if exceptions is not None:
            for exception_group in exceptions:
                for exception_name, exception_configuration in exception_group.items():
                    if not exception_name in EXCEPTIONS:
                        EXCEPTIONS[exception_name] = exception_configuration
                    else:
                        self.log.error('Duplicate exception name for %s'%exception_name)

    def error(self,message):
        if self.log: self.log.error(message)

    def info(self,message):
        if self.log: self.log.info(message)

    def prepare_api(self,configuration):
        self.set_configuration(configuration)

        self.config.info('Configurating API from configuration %s ...'%self.config.config_file)

        template_path = alphaz.__file__.replace('__init__.py','') + 'templates'
        self.api            = AlphaFlask(__name__,
            template_folder=template_path,
            static_folder=template_path,
            root_path=template_path)

        self.ma = self.api.ma
            
        # Cnx
        db_cnx              = self.config.db_cnx

        if db_cnx is None:
            self.error('Databases are not configurated in config file %s'%self.config.filepath)
            exit()

        if not 'main' in db_cnx:
            self.config.show()
            self.config.error('Missing <main> database configuration')
            exit()

        self.api.set_databases(db_cnx)

        # databases
        db_logger           = self.config.get_logger('database')
        if db_logger is None:
            db_logger       = self.config.get_logger('main')

        for name, cf in db_cnx.items():
            log = self.config.get_logger(cf['logger']) if 'logger' in cf else db_logger
            self.databases[name] = AlphaDatabase(self.api,name=name,config=cf,log=log)
        self.db = self.databases['main']

        # configuration
        self.api.log: AlphaLogger    = self.get_logger('api')

        api_root = self.config.get('api_root')
        self.api.set_config('api',self.configuration,root=api_root if api_root is not None else self.root)
        self.api.db = self.db

        models_sources = self.api.conf.get('directories/database_models')
        if not models_sources:
            self.api.log.error('Missing <directories/database_models> entry in configuration %s'%self.api.conf.filepath)
            exit()

        models_sources.append("alphaz.models.database.main_definitions")

        modules             = flask_lib.get_definitions_modules(models_sources,log=self.log)

    def get_database(self,name=None) -> AlphaDatabase:
        if self.api is None:
            # required for database cnx
            self.prepare_api(self.configuration)

        if name is None or name == 'main':
            return self.db

        if name == "users" and not 'users' in self.databases:
            return self.db

        if name in self.databases:
            return self.databases[name]

        return self.config.get_database(name)
                
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
        self.check_configuration()
        return self.config.get_logger(*args,**kwargs)

    def check_configuration(self):
        if self.config is None:
            self.set_configuration(None)
            if self.config is None:
                print('ERROR: Configuration need to be initialized')
                exit()