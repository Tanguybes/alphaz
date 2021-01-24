import os, sys, datetime, glob, importlib, inspect, warnings
from typing import List, Dict
with warnings.catch_warnings():
     from flask_marshmallow import Marshmallow

from ....models.main import AlphaClass
from ....models.logger import AlphaLogger
from ....libs import io_lib, flask_lib

from ....models.config import AlphaConfig
from ....models import database as database_models
from ....models.main import AlphaException
from ...api import AlphaFlask

from ...database.structure import AlphaDatabase

from ....utils.tasks import start_celery

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

        self.ma:Marshmallow         = None
        self.db:AlphaDatabase       = None
        self.api:AlphaFlask         = None

        self.models_sources: List[str] = []
        self.models_source_loaded:bool = False
        
        configuration = None
        if 'ALPHA_CONF' in os.environ:
            configuration = os.environ['ALPHA_CONF']
        self.configuration: str     = configuration
        self.configuration_name: str = configuration

        self.config:AlphaConfig     = AlphaConfig('config',
            root=self.root,
            configuration=configuration,
            core=self
        )

    def set_configuration(self,configuration_name):
        if configuration_name is None and self.config.configuration is not None:
            configuration_name = self.config.configuration
            
        self.config.set_configuration(configuration_name)
        self.configuration     = configuration_name
        self.configuration_name = configuration_name

    def prepare_api(self,configuration):
        if self.api is not None:
            return 

        self.set_configuration(configuration)

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
        self.api.log_requests: AlphaLogger    = self.get_logger('http')

        api_root = self.config.get('api_root')
        self.api.set_config(name='api',
            configuration=self.configuration,
            root=api_root if api_root is not None else self.root
        )
        self.api.db = self.db
        
        """# ensure tests
        self.db.ensure("tests", drop=True)
        self.db.ensure("files_process")"""

    def get_database(self, name=None) -> AlphaDatabase:
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
        self.load_models_sources()
        
        table = table.upper()
        if type(schema) != str and hasattr(schema,"name"):
            schema = schema.name
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
        if table_object is None and table in flask_lib.TABLES["main"]['tables']:
            table_object = flask_lib.TABLES["main"]['tables'][table]
        if table_object is None:
            raise AlphaException('cannot_find_table', parameters={'table':table})

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

    def load_models_sources(self):
        if not self.models_source_loaded:
            self.models_sources = self.config.get('directories/database_models')
            if not self.models_sources:
                self.log.error('Missing <directories/database_models> entry in configuration %s'%self.conf.filepath)
                exit()

            self.models_sources.append("alphaz.models.database.main_definitions")
            modules             = flask_lib.get_definitions_modules(self.models_sources, log=self.log)