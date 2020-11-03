import os, sys, datetime, glob, importlib, inspect
from typing import List, Dict
from flask_marshmallow import Marshmallow

from ....models.main import AlphaClass
from ....utils.logger import AlphaLogger
from ....config.config import AlphaConfig
from ....libs import io_lib, flask_lib
from ....models import database as database_models
from ....models.main._exception import EXCEPTIONS
from ....models.main import AlphaException
from ...api import AlphaFlask

from ...database.structure import AlphaDatabase

from . import _utils

import alphaz

def _get_relative_path(file: str, level = 0, add_to_path=True):
    if level == 0:
        root                    = os.path.dirname(file)
    else:
        root                    = os.sep.join(os.path.dirname(file).split(os.sep)[:-level])
    if add_to_path:
        sys.path.append(root)
    return root

class AlphaCore(AlphaClass): 
    instance    = None

    def __init__(self,file:str,level:int=0,*args,**kwargs): 
        super().__init__(log=None)

        self.root: str               = _get_relative_path(file, level=level)
        self.config:AlphaConfig     = None

        self.loggers: {AlphaLogger} = {}
        self.initiated: bool        = False
        self.databases: dict        = {}
        self.configuration: str     = None
        self.configuration_name: str = None
        self.ma:Marshmallow         = None
        self.db:AlphaDatabase       = None
        self.api:AlphaFlask         = None
        self.models_sources: List[str] = []
        
        configuration = None
        if 'ALPHA_CONF' in os.environ:
            configuration = os.environ['ALPHA_CONF']

        self.config:AlphaConfig     = AlphaConfig('config',
            root=self.root,
            configuration=configuration
        )

    def set_configuration(self,configuration_name):
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

    def prepare_api(self,configuration):
        self.set_configuration(configuration)

        self.config.info('Configurating API from configuration %s ...'%self.config.filepath)

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
            self.databases[name] = AlphaDatabase(self.api,name=name,config=cf,log=log,main=cf==db_cnx['main'])
        self.db = self.databases['main']

        # configuration
        self.api.log: AlphaLogger    = self.get_logger('api')

        api_root = self.config.get('api_root')
        self.api.set_config(name='api',
            configuration=self.configuration,
            root=api_root if api_root is not None else self.root
        )
        self.api.db = self.db

        self.models_sources = self.api.conf.get('directories/database_models')
        if not self.models_sources:
            self.api.log.error('Missing <directories/database_models> entry in configuration %s'%self.api.conf.filepath)
            exit()

        self.models_sources.append("alphaz.models.database.main_definitions")
        
        """# ensure tests
        self.db.ensure("tests", drop=True)
        self.db.ensure("files_process")"""

    def get_database(self, name=None) -> AlphaDatabase:
        if self.api is None:
            # required for database cnx
            self.prepare_api(self.configuration)

        if name is None or name == 'main':
            return self.db

        if name == "users" and 'users' not in self.databases:
            return self.db

        if name in self.databases:
            return self.databases[name]

        return self.config.get_database(name)
                
    def get_logger(self,*args, **kwargs) -> AlphaLogger:
        self._check_configuration()
        return self.config.get_logger(*args,**kwargs)

    def _check_configuration(self):
        if self.config is None:
            self.set_configuration(None)
            if self.config is None:
                print('ERROR: Configuration need to be initialized')
                exit()

    def get_table(self,schema:str, table:str):
        table = table.upper()
        if not schema in flask_lib.TABLES:
            raise AlphaException('schema_not_loaded', parameters={'schema':schema})

        """if table in flask_lib.TABLES:
            obj = flask_lib.TABLES[table]
            obj.__table__.drop()
            api.set_data("%s dropped"%table)"""

        tables = flask_lib.TABLES[schema]['tables']
        if not table in tables:
            raise AlphaException('cannot_find_table', parameters={'table':table})

        table_object = tables[table]
        table_object.bind = flask_lib.TABLES[schema]['db']
        
        """if not table in db.metadata.tables:
            raise AlphaException('cannot_find_table',parameters={'table':table})

        table_object = db.metadata.tables[table]"""
        return table_object

    def create_table(self,schema:str,table_name:str):
        modules             = flask_lib.get_definitions_modules(self.models_sources, log=self.log)
        table_object        = self.get_table(schema, table_name)
        table_object.__table__.create(table_object.bind._engine)
        
    def drop_table(self,schema:str,table_name:str):
        modules             = flask_lib.get_definitions_modules(self.models_sources, log=self.log)
        table_object        = self.get_table(schema, table_name)
        table_object.__table__.drop(table_object.bind._engine)