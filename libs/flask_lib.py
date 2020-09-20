import inspect, glob, os, importlib

from flask_admin.contrib.sqla import ModelView
from flask import Markup

from ..utils import *

from ..utils.logger import AlphaLogger
from ..models.database.structure import AlphaDatabaseNew

from sqlalchemy.orm.attributes import InstrumentedAttribute

TABLES = {}

def load_views(module:ModuleType) -> List[ModelView]:
    """[Load view from tables definitions module]

    Args:
        module (ModuleType): [description]

    Returns:
        List[ModelView]: [description]
    """
    db = module.db
    
    db_classes_names = [m[0] for m in inspect.getmembers(module, inspect.isclass) if m[1].__module__ == module.__name__]

    view_config = {
    }

    views = []
    db_classe_names = []
    for db_classe_name in db_classes_names:
        class_object = getattr(module,db_classe_name)
        if db_classe_name in db_classe_names: continue
        db_classe_names.append(db_classe_name)

        if not db_classe_name in view_config:
            if '__tablename__' in class_object.__dict__:
                database_name   = "main" if not hasattr(class_object,"__bind_key__") else class_object.__bind_key__
                name        = '%s:%s'%(database_name,class_object.__tablename__)
                #if print('Add view %s for %s'%(class_object.__tablename__,class_object.__bind_key__))

                attributes                  = [x for x,y in class_object.__dict__.items() if isinstance(y,InstrumentedAttribute)]

                view = ModelView(
                    class_object,
                    db.session,
                    name=class_object.__tablename__,
                    category=database_name,
                    endpoint=name)
                view.column_list    = attributes
                views.append(view)
        else:
            views.append(view_config[db_classe_name](class_object,db.session))
    
    return views

def get_definitions_modules(modules_list:List[ModuleType],log:AlphaLogger) -> List[ModuleType]:
    """[Get database table definitions from parent or children module list]

    Args:
        modules_list (List[ModuleType]): [parent or children module list]
        log (AlphaLogger): [description]

    Returns:
        List[ModuleType]: [description]
    """
    from alphaz.models.database.models import AlphaTable

    modules = []

    for module_r in modules_list:
        module = importlib.import_module(module_r) if type(module_r) == str else module_r
        
        if not module:
            log.error('Cannot load module <%s>'%module_r)
            continue

        dir_ini = module.__file__ and '__init__.py' in module.__file__
        dir_path = hasattr(module,'__path__') and module.__path__ and module.__path__._path and len(module.__path__._path) != 0

        if dir_ini or dir_path:
            if dir_ini:
                sub_files   = glob.glob(module.__file__.replace('__init__','*'))
            else:
                sub_files   = glob.glob(module.__path__._path[0] + os.sep + '*')

            names       = [os.path.basename(x).replace('.py','') for x in sub_files if not '__init__' in x]

            for sub_file_name in names:
                try:
                    sub_module = importlib.import_module("%s.%s"%(module.__name__,sub_file_name))
                except Exception as ex:
                    log.error('Cannot load module %s.%s:\n   %s'%(module.__name__,sub_file_name,ex))
                    continue
                
                if not 'db' in sub_module.__dict__: continue
                db = sub_module.__dict__['db']

                if not db.name in TABLES:
                    TABLES[db.name] = {}

                found = False
                for name, obj in sub_module.__dict__.items():
                    if inspect.isclass(obj) and issubclass(obj,AlphaTable) and hasattr(obj,'__tablename__'):
                        table = obj
                        found = True

                        TABLES[db.name][obj.__tablename__] = obj
                
                if found:
                    modules.append(sub_module)
        else:
            if not 'db' in module.__dict__: continue
            db = module.__dict__['db']

            if not db.name in TABLES:
                TABLES[db.name] = {}

            for name, obj in module.__dict__.items():
                if inspect.isclass(obj) and issubclass(obj,AlphaTable) and hasattr(obj,'__tablename__'):
                    table = obj
                    found = True

                    TABLES[db.name][obj.__tablename__] = obj
            
            if found:
                modules.append(module)
    return modules
