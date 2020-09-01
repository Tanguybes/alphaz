from flask_admin.contrib.sqla import ModelView
from flask import Markup

from types import ModuleType

from ..models.database.structure import AlphaDatabaseNew

import inspect

def load_views(module:ModuleType) -> list:
    """[Load view from tables definitions module]

    Args:
        module (ModuleType): [description]

    Returns:
        list: [description]
    """
    db_classes_names = [m[0] for m in inspect.getmembers(module, inspect.isclass) if m[1].__module__ == module.__name__]

    view_config = {
    }

    views = []
    for db_classe_name in db_classes_names:
        class_object = getattr(module,db_classe_name)

        if not db_classe_name in view_config:
            if '__tablename__' in class_object.__dict__:
                views.append(ModelView(class_object,db.session))
        else:
            views.append(view_config[db_classe_name](class_object,db.session))
    return views

    def get_definitions_modules(self,modules_list:list,log):
        from alphaz.models.database.models import AlphaModel

        modules = []

        for module in modules_list:
            if '__init__.py' in module.__file__:
                sub_files   = glob.glob(module.__file__.replace('__init__','*'))
                names       = [os.path.basename(x).replace('.py','') for x in sub_files if not '__init__' in x]

                for sub_file_name in names:
                    try:
                        sub_module = importlib.import_module("%s.%s"%(module.__name__,sub_file_name))
                    except:
                        log.error('Cannot load module %s.%s'%(module.__name__,sub_file_name))
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