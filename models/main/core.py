import os, sys, datetime
from ...utils.logger import AlphaLogger
from ...config.config import AlphaConfig
from ..database.structure import AlphaDatabaseNew
from ...libs import io_lib

from flask_marshmallow import Marshmallow
from ..api.structures import AlphaFlask
from flask_admin import Admin

#from ..database.definitions import Base

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
        self.api            = AlphaFlask(__name__)

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
            self.prepare_api()

        if name is None:
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

    def init_admin_view(self,views):
        api_name            = self.config.get('api/name')
        self.admin_db       = Admin(self.api, name=api_name, template_mode='bootstrap3')
        for view in views:  
            self.admin_db.add_view(view)

    def init_database(self,models_modules:list,name='main',drop=True):
        #if drop:
        #    self.db.drop_all()
        self.db.create_all()
        
        init_database_config = self.config.get('databases/%s/init'%name)
        
        if init_database_config is None:
            return 

        for table, cf in init_database_config.items():
            class_name      = ''.join([x.capitalize() for x in table.split('_')])

            self.log.info('Initiating table %s from %s'%(class_name,name))

            class_instance = None
            for models_module in models_modules:
                if hasattr(models_module,class_name):
                    class_instance  = getattr(models_module,class_name)
                else:
                    continue
            if class_instance is None:
                self.log.error('Missing model module')
                continue

            is_file         = os.path.isfile(cf)
            data            = io_lib.read_json(cf)

            for row_column in data:
                converted_columns = {}
                for key, row_entry in row_column.items():
                    if type(row_entry) == str and len(row_entry) > 7 and row_entry[4] == '/' and row_entry[7] == '/':
                        row_entry = datetime.datetime.strptime(row_entry, '%Y/%m/%d')
                    converted_columns[key] = row_entry

                #db.session.query(class_instance).delete()
                row = class_instance(**converted_columns)

                try:
                    self.db.session.add(row)
                    self.db.session.commit()
                except Exception as e:
                    print('ERROR:',e)
                    exit()