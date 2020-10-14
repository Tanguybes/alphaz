import inspect, glob, os, importlib

from flask_admin.contrib.sqla import ModelView
from flask import Markup

from ..utils import *

from ..utils.logger import AlphaLogger
from ..models.database.structure import AlphaDatabase

from sqlalchemy.orm.attributes import InstrumentedAttribute

TABLES = {}


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

    loaded_modules = []

    for module_r in modules_list:
        module = importlib.import_module(module_r) if type(module_r) == str else module_r
        
        if not module:
            log.error('Cannot load module <%s>'%module_r)
            continue

        dir_ini = module.__file__ and '__init__.py' in module.__file__
        if dir_ini:
            module_path = module.__file__.replace('__init__','*')

        dir_path = hasattr(module,'__path__') and module.__path__
        if dir_path and hasattr(module.__path__,'_path'):
            dir_path    = module.__path__._path and len(module.__path__._path) != 0
            module_path = module.__path__._path[0] + os.sep + '*'
        elif dir_path:
            dir_path    = len(module.__path__) != 0
            module_path = module.__path__[0] + os.sep + '*'

        if dir_ini or dir_path:
            sub_files   = glob.glob(module_path) if dir_ini else glob.glob(module_path)

            names       = [os.path.basename(x).replace('.py','') for x in sub_files if not '__init__' in x and '.py' in x]

            for sub_file_name in names:
                module_full_name = "%s.%s"%(module.__name__,sub_file_name)
                if module_full_name in loaded_modules: continue

                loaded_modules.append(module_full_name)
                try:
                    sub_module = importlib.import_module(module_full_name)
                except Exception as ex:
                    log.error('Cannot load module %s'%(module_full_name),ex=ex)
                    continue
                
                if not 'db' in sub_module.__dict__: continue
                db = sub_module.__dict__['db']

                if not db.name in TABLES:
                    TABLES[db.name] = {'db':db,'tables':{}}

                found = False
                for name, obj in sub_module.__dict__.items():
                    if inspect.isclass(obj) and issubclass(obj,AlphaTable) and hasattr(obj,'__tablename__'):
                        table = obj
                        found = True

                        TABLES[db.name]['tables'][obj.__tablename__] = obj
                
                if found:
                    modules.append(sub_module)
        else:
            if not 'db' in module.__dict__: continue
            db = module.__dict__['db']

            if not db.name in TABLES:
                TABLES[db.name] = {'db':db,'tables':{}}

            for name, obj in module.__dict__.items():
                if inspect.isclass(obj) and issubclass(obj,AlphaTable) and hasattr(obj,'__tablename__'):
                    table = obj
                    found = True

                    TABLES[db.name]['tables'][obj.__tablename__] = obj
            
            if found:
                modules.append(module)

    return modules

class AlphaModelView(ModelView):
    column_display_pk = True

def load_views() -> List[ModelView]:
    """[Load view from tables definitions module]

    Args:
        module (ModuleType): [description]

    Returns:
        List[ModelView]: [description]
    """
    views = []
    
    for schema, cf in TABLES.items():           
        db, tables = cf['db'], cf['tables']

        for table_name, class_object in tables.items():
            attributes                  = [x for x,y in class_object.__dict__.items() if isinstance(y,InstrumentedAttribute)]

            name        = '%s:%s'%(schema,class_object.__tablename__)
            view = AlphaModelView(
                class_object,
                db.session,
                name=class_object.__tablename__,
                category=schema,
                endpoint=name)

            view.column_list    = attributes
            views.append(view)
    return views
