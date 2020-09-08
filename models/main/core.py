import os, sys, datetime, glob, importlib, inspect

from ...utils.logger import AlphaLogger
from ...config.config import AlphaConfig
from ...libs import io_lib, flask_lib, database_lib
from ...models import database as database_models

from ..api.structures import AlphaFlask
from ..database.structure import AlphaDatabaseNew

from flask_marshmallow import Marshmallow
from flask_admin import Admin    

from itertools import chain

class AlphaCore: 
    instance                = None

    api         = None
    db          = None
    admin_db    = None
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
        environs            = self.config.get('environment')

        if environs:
            for key, value in environs.items():
                os.environ[key] = value

        loggers_config      = self.config.get("loggers")

        self.loggers        = self.config.loggers

        self.log            = self.config.get_logger('main')

    def prepare_api(self):
        self.config.info('Configuring API for configuration %s ...'%self.config.config_file)
        self.api            = AlphaFlask(__name__,template_folder=self.root + os.sep + 'templates')

        #self.config.api     = self.api
        db_cnx              = self.config.db_cnx
        if db_cnx is None:
            self.error('Databases not configurated in config file')

        if 'main' in db_cnx:
            uri = db_cnx['main']['cnx']
            if ':///' in uri:
                io_lib.ensure_file(uri.split(':///')[1])
            db_type = db_cnx['main']['type']

            self.api.config['SQLALCHEMY_DATABASE_URI'] = uri
        else:
            self.config.show()
            self.config.error('Missing <main> database configuration')

        for key, cf_db in db_cnx.items():
            self.api.config['SQLALCHEMY_BINDS'] = {x:y['cnx'] for x,y in db_cnx.items() if x != 'main'}

        self.api.config['MYSQL_DATABASE_CHARSET']           = 'utf8mb4'
        self.api.config['QLALCHEMY_TRACK_MODIFICATIONS']    = True
        #self.api.config['EXPLAIN_TEMPLATE_LOADING']         = True
        self.api.config['UPLOAD_FOLDER']                    = self.root + os.sep + 'templates'

        db_logger           = self.config.get_logger('database')
        if db_logger is None:
            db_logger       = self.config.get_logger('main')

        self.db             = AlphaDatabaseNew(self.api,name="main",log=db_logger,config=db_cnx['main'])

        self.ma             = Marshmallow(self.api)
        #self.api.db         = self.db

        #Base.prepare(self.db.engine, reflect=True)

        #set_alpha_tables(self.db)

        for name, cf in db_cnx.items():
            self.databases[name] = AlphaDatabaseNew(self.api,name=name,log=db_logger,config=cf)

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
                print('Configuration need to be initialized')
                exit()

    def init_admin_view(self,models_sources):
        modules             = flask_lib.get_definitions_modules(models_sources,log=self.log)

        views               = list(chain(*[flask_lib.load_views(module=x) for x in modules]))
        endpoints           = [x.endpoint for x in views]

        from alphaz.models.database.views import views as alpha_views
        for view in alpha_views:
            if view.endpoint not in endpoints:
                views.append(view)

        api_name            = self.config.get('api/name')
        self.admin_db       = Admin(self.api, name=api_name, template_mode='bootstrap3')
        
        self.admin_db.add_views(*views)

    def init_database(self,models_sources=[],databases=None,drop=False):

        modules             = flask_lib.get_definitions_modules(models_sources,log=self.log)
        from alphaz.models.database import main_definitions

        #if drop:
        #    self.db.drop_all()
        init_database_config = self.config.get('databases')

        if init_database_config is None:
            self.log.error('No initialisation configuration has been set in "databases')
            return 

        initiated = []
        for database_name, cf in init_database_config.items():
            if databases is not None and database_name not in databases: continue
            if type(cf) != dict: continue

            db = self.get_database(database_name)

            self.log.info('Creating database %s'%database_name)
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
                    self.process_databases_init(file_path,models_sources,file_type='json')

            # python ini
            if 'init_database_dir_py' in cf:
                py_ini      = cf['init_database_dir_py']
                files       = [ x for x in glob.glob(py_ini + os.sep + '*.py') if not '__init__' in x]

                self.log.info('Initiating table %s from python files (%s): \n%s'%(database_name,py_ini,'\n'.join(['   - %s'%x for x in files])))
                for file_path in files:
                    self.process_databases_init(file_path,models_sources)

    def process_databases_init(self,file_path,models_sources,file_type='py'):
        if not database_models in models_sources: models_sources.append(database_models)

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

                self.get_entries(models_sources,file_path,ini)
        elif file_type =='json':
            try:
                ini = io_lib.read_json(file_path)
            except:
                self.log.error('Cannot read file %s'%(file_path))
                return
            self.get_entries(models_sources,file_path,ini)

    def get_entries(self,models_sources,file_path,configuration):
        from alphaz.models.database.models import AlphaModel

        for database, tables_config in configuration.items():
            db = database
            if type(database) == str:
                db = self.get_database(database)
                if db is None:
                    self.log.error('In file %s configuration database <%s> is not recognized'%(file_path,database))
                    continue

            if type(tables_config) != dict: 
                self.log.error('In file %s configuration of database %s must be of type <dict>'%(file_path,database))
                continue

            for table, config in tables_config.items():
                table_name = table
                if type(table) == str:
                    found = False
                    for model in models_sources:
                        for name, obj in model.__dict__.items():
                            if inspect.isclass(obj) and issubclass(obj,AlphaModel) and hasattr(obj,'__tablename__') and table == obj.__tablename__:
                                table = obj
                                found = True
                        
                        if not found and '__init__.py' in model.__file__:
                            sub_files   = glob.glob(model.__file__.replace('__init__','*'))
                            names       = [os.path.basename(x).replace('.py','') for x in sub_files if not '__init__' in x]

                            for sub_file_name in names:
                                try:
                                    sub_model = importlib.import_module("%s.%s"%(model.__name__,sub_file_name))
                                except:
                                    self.log.error('In file %s configuration of database %s cannot import <%s> from <%s>'%(file_path,database,sub_file_name,model.__name__))
                                    continue

                                for name, obj in sub_model.__dict__.items():
                                    if inspect.isclass(obj) and issubclass(obj,AlphaModel) and hasattr(obj,'__tablename__') and table == obj.__tablename__:
                                        table = obj
                                        found = True

                    if not found:
                        self.log.error('In file <%s> configuration of database <%s> the table <%s> is not found'%(file_path,database,table))
                        continue
                else:
                    table_name = table.__tablename__
                
                if 'headers' in config and 'values' in config:
                    if type(config['values']) != list: 
                        self.log.error('In file %s "values" key from table %s and database %s must be of type <list>'%(file_path,table_name,database))
                        continue
                    if type(config['headers']) != list: 
                        self.log.error('In file %s "headers" key from table %s and database %s must be of type <list>'%(file_path,table_name,database))
                        continue

                    headers_size = len(config['headers'])

                    entries = []
                    for entry in config['values']:
                        if type(entry) != list:
                            self.log.error('In file %s from table %s and database %s entry %s must be of type <list>'%(file_path,table_name,database,entry))
                            continue
                        entries.append(entry)

                    self.log.info('Adding %s entries from <list> for table %s in database %s from file %s'%(len(entries),table_name,database,file_path))
                    database_lib.process_entries(models_sources,db,table,self.log,headers=config['headers'],values=entries)

                if 'objects' in config:
                    entries = config['objects']
                    self.log.info('Adding %s entries from <objects> for table %s in database %s from file %s'%(len(entries),table_name,database,file_path))
                    database_lib.process_entries(models_sources,db,table,self.log,values=entries)