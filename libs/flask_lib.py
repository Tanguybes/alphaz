import inspect, glob, os, importlib

from flask_admin.contrib.sqla import ModelView
from flask import Markup
from typing import List
from types import ModuleType

from ..utils.logger import AlphaLogger
from ..models.database.structure import AlphaDatabaseNew

from sqlalchemy.orm.attributes import InstrumentedAttribute

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
    from alphaz.models.database.models import AlphaModel

    modules = []

    for module in modules_list:
        if '__init__.py' in module.__file__:
            sub_files   = glob.glob(module.__file__.replace('__init__','*'))
            names       = [os.path.basename(x).replace('.py','') for x in sub_files if not '__init__' in x]

            for sub_file_name in names:
                try:
                    sub_module = importlib.import_module("%s.%s"%(module.__name__,sub_file_name))
                except Exception as ex:
                    log.error('Cannot load module %s.%s:\n   %s'%(module.__name__,sub_file_name,ex))
                    continue
                
                found = False
                for name, obj in sub_module.__dict__.items():
                    if inspect.isclass(obj) and issubclass(obj,AlphaModel) and hasattr(obj,'__tablename__'):
                        table = obj
                        found = True
                
                if found:
                    modules.append(sub_module)
        else:
            for name, obj in module.__dict__.items():
                if inspect.isclass(obj) and issubclass(obj,AlphaModel) and hasattr(obj,'__tablename__'):
                    table = obj
                    found = True
            
            if found:
                modules.append(module)
    return modules