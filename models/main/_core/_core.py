import os, sys, datetime, glob, importlib, inspect

from ....utils.logger import AlphaLogger
from ....config.config import AlphaConfig
from ....libs import io_lib, flask_lib, database_lib
from ....models import database as database_models
from ....models.main._exception import EXCEPTIONS

from ...api import AlphaFlask
from ...database.structure import AlphaDatabaseNew

from . import _utils

import alphaz

class AlphaCore: 
    instance                = None

    api         = None
    db          = None
    ma          = None

    databases   = {}

    def __init__(self,file:str): 
        self.root:str               = self.get_relative_path(file, level=0)
        self.config                 = None
        self.log: AlphaLogger       = None
        self.loggers: {AlphaLogger} = {}
        self.initiated: bool        = False
        self.databases: dict        = {}
        self.configuration: str     = None

    def set_configuration(self,configuration_name):
        self.config         = AlphaConfig('config',root=self.root,configuration=configuration_name)
        self.configuration  = self.config.configuration

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

        self.config.info('Configuring API from configuration %s ...'%self.config.config_file)

        template_path = alphaz.__file__.replace('__init__.py','') + 'templates'
        self.api            = AlphaFlask(__name__,
            template_folder=template_path,
            static_folder=template_path,
            root_path=template_path)

        self.ma = self.api.ma
            
        # Cnx
        db_cnx              = self.config.db_cnx

        if db_cnx is None:
            self.error('Databases not configurated in config file')

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
            self.databases[name] = AlphaDatabaseNew(self.api,name=name,config=cf,log=log)
        self.db = self.databases['main']

        # configuration
        self.api.log: AlphaLogger    = self.get_logger('api')
        self.api.set_config('api',self.configuration)
        self.api.db = self.db

        models_sources = self.api.conf.get('database_models')
        models_sources.append("alphaz.models.database.main_definitions")

        modules             = flask_lib.get_definitions_modules(models_sources,log=self.log)

    def get_database(self,name=None) -> AlphaDatabaseNew:
        if self.api is None:
            # required for database cnx
            self.prepare_api()

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

    def init_databases(self,databases=None,drop=False): # Todo: remove database ?
        initialisation = self.api.conf.get('initialisation')
        if not initialisation: return 

        all_schemas = 'all' in initialisation and initialisation['all']
        all_drop    = 'drop' in initialisation and initialisation['drop']
        if not all_schemas:
            schemas = {x:y for x,y in initialisation.items() if x not in ['all','drop']}

        #if len([x for x in databases if x is not None]) == 0: return

        #from alphaz.models.database import main_definitions

        #if drop:
        #    self.db.drop_all()
        init_database_config = self.config.get('databases')

        if init_database_config is None:
            self.log.error('No initialisation configuration has been set in "databases')
            return 

        initiated = []
        for database_name, cf in init_database_config.items():
            if not all_schemas and database_name not in schemas: continue

            if type(cf) != dict: continue

            if 'main' in init_database_config and init_database_config['main'] == database_name:
                if all_drop:
                    self.log.info('Drop <%s> database'%database_name)
                    self.db.drop_all()
                self.log.info('Creating database <main>')
                for k,l in self.db.get_binds().items():
                    print('     {:30}  {}'.format(str(k),str(l)))
                    
                self.db.create_all()
                self.db.commit()

            db = self.get_database(database_name)

            if all_drop:
                self.log.info('Drop <%s> database'%database_name)
                db.drop_all()

            self.log.info('Creating database <%s>'%database_name)

            for k,l in db.get_binds().items():
                print('     > {:30}  {}'.format(str(k),str(l)))

            db.create_all()
            db.commit()

            #class_name      = ''.join([x.capitalize() for x in table.split('_')])
            if not type(cf) == dict:    continue
            if not 'ini' in cf or not cf['ini']:           continue

            # json ini
            if 'init_database_dir_json' in cf:
                json_ini    = cf['init_database_dir_json']
                files       = glob.glob(json_ini + os.sep + '*.json')

                self.log.info('Initiating table %s from json files (%s): \n%s'%(database_name,json_ini,'\n'.join(['   - %s'%x for x in files])))
                for file_path in files:
                    self.process_databases_init(file_path,file_type='json')

            # python ini
            if 'init_database_dir_py' in cf:
                py_ini      = cf['init_database_dir_py']
                files       = [ x for x in glob.glob(py_ini + os.sep + '*.py') if not '__init__' in x]

                self.log.info('Initiating table %s from python files (%s): \n%s'%(database_name,py_ini,'\n'.join(['   - %s'%x for x in files])))
                for file_path in files:
                    self.process_databases_init(file_path,models_sources)

    def process_databases_init(self,file_path,file_type='py'):
        if file_type == "py":
            current_path    = os.getcwd()
            module_path     = file_path.replace(current_path,'').replace('/','.').replace('\\','.').replace('.py','')

            if module_path[0] == '.':
                module_path = module_path[1:]

            module          = importlib.import_module(module_path)

            if hasattr(module,'ini'):
                ini = module.__dict__['ini']
                if type(ini) != dict: 
                    self.log.error('In file %s <ini> configuration must be of type <dict>'%(file_path))
                    return

                self.get_entries(file_path,ini)
        elif file_type =='json':
            try:
                ini = io_lib.read_json(file_path)
            except:
                self.log.error('Cannot read file %s'%(file_path))
                return
            self.get_entries(file_path,ini)

    def get_entries(self,file_path,configuration):
        from alphaz.models.database.models import AlphaTable

        #models_sources = [importlib.import_module(x) if type(x) == str else x for x in models_sources]

        for database, tables_config in configuration.items():
            db = database
            if type(database) == str:
                db = self.get_database(database)
                if db is None:
                    self.log.error('In file %s configuration database <%s> is not recognized'%(file_path,database))
                    continue

            if type(tables_config) != dict: 
                self.log.error('In file %s configuration of database <%s> must be of type <dict>'%(file_path,database))
                continue

            for table, config in tables_config.items():
                table_name = table
                found = False
                for schema, tables in flask_lib.TABLES.items():           
                    if table in tables['tables']:
                        found = True
                        table = tables['tables'][table]

                if not found:
                    self.log.error('In file %s configuration of database <%s> the table <%s> is not found'%(file_path,database,table))
                    continue
                
                if 'headers' in config and 'values' in config:
                    if type(config['values']) != list: 
                        self.log.error('In file %s "values" key from table <%s> and database <%s> must be of type <list>'%(file_path,table_name,database))
                        continue
                    if type(config['headers']) != list: 
                        self.log.error('In file %s "headers" key from table <%s> and database <%s> must be of type <list>'%(file_path,table_name,database))
                        continue

                    headers_size = len(config['headers'])

                    entries = []
                    for entry in config['values']:
                        if type(entry) != list:
                            self.log.error('In file %s from table <%s> and database <%s> entry <%s> must be of type <list>'%(file_path,table_name,database,entry))
                            continue
                        entries.append(entry)

                    self.log.info('Adding %s entries from <list> for table <%s> in database <%s> from file %s'%(len(entries),table_name,database,file_path))
                    database_lib.process_entries(db,table,self.log,headers=config['headers'],values=entries)

                if 'objects' in config:
                    entries = config['objects']
                    self.log.info('Adding %s entries from <objects> for table <%s> in database <%s> from file %s'%(len(entries),table_name,database,file_path))
                    database_lib.process_entries(db,table,self.log,values=entries)