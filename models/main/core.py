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
    root: str               = None
    initiated: bool         = False
    loggers: {AlphaLogger}  = {}
    log: AlphaLogger        = None

    instance                = None

    api         = None
    db          = None
    admin_db    = None
    ma          = None

    def __init__(self,file:str):   
        root                = self.get_relative_path(file, level=0)

        self.config         = AlphaConfig('config',root=root)

        logs_directory      = self.config.get("log_directory")
        loggers_config      = self.config.get("loggers")

        self.loggers        = self.config.loggers

    def prepare_api(self):
        self.config.info('Configuring API for configuration %s ...'%self.config.config_file)
        self.api            = AlphaFlask(__name__)

        #self.config.api     = self.api
        db_cnx              = self.config.db_cnx

        db_type             = 'mysql'
        if 'main' in db_cnx:
            uri = db_cnx['main']['cnx']
            if ':///' in uri:
                io_lib.ensure_file(uri.split(':///')[1])
            db_type = db_cnx['main']['type']
            print('Using %s database'%uri)

            self.api.config['SQLALCHEMY_DATABASE_URI'] = uri
        else:
            self.config.show()
            self.config.error('Missing <main> database configuration')

        for key, cf_db in db_cnx.items():
            self.api.config['SQLALCHEMY_BINDS'] = {x:y['cnx'] for x,y in db_cnx.items() if x != 'main'}

        db_logger           = self.config .get_logger('database')
        if db_logger is None:
            db_logger       = self.config .get_logger('main')


        self.db             = AlphaDatabaseNew(self.api,log=db_logger,db_type=db_type)

        self.ma             = Marshmallow(self.api)

        self.api.db         = self.db

        #Base.prepare(self.db.engine, reflect=True)

        #set_alpha_tables(self.db)
                
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
        return self.config.get_logger(*args,**kwargs)

    def get_database(self,*args, **kwargs):
        return self.config.get_database(*args,**kwargs)

    def init_admin_view(self,views):
        api_name            = self.config.get('api/name')
        self.admin_db       = Admin(self.api, name=api_name, template_mode='bootstrap3')
        for view in views:  
            self.admin_db.add_view(view)

    def set_configuration(self,configuration_name):
        self.config.set_configuration(configuration_name)

    def init_database(self,models_module,name='main',drop=True):
        if drop:
            self.db.drop_all()
        self.db.create_all()
        
        init_database_config = self.config.get('databases/%s/init'%name)
        
        for table, cf in init_database_config.items():
            class_name      = ''.join([x.capitalize() for x in table.split('_')])
            class_instance  = getattr(models_module,class_name)
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
                    print('error',e)
                    exit()