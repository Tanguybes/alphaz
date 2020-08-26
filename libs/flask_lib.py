from flask_admin.contrib.sqla import ModelView
from flask import Markup

from types import ModuleType

from ..models.database.structure import AlphaDatabaseNew

import inspect

def load_views(module:ModuleType,db:AlphaDatabaseNew) -> list:
    """[Load view from tables definitions module]

    Args:
        module (ModuleType): [description]
        db (AlphaDatabaseNew): [description]

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