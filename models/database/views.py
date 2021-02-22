import inspect

from flask_admin.contrib.sqla import ModelView
from flask import Markup

from core import core

db = core.get_database()

from . import main_definitions as defs

db_classes_names = [
    m[0]
    for m in inspect.getmembers(defs, inspect.isclass)
    if m[1].__module__ == defs.__name__
]

view_config = {}

views = []
for db_classe_name in db_classes_names:
    if not db_classe_name in view_config:
        class_object = getattr(defs, db_classe_name)
        if "__tablename__" in class_object.__dict__:
            base_name = "ALPHA"
            name = "%s:%s" % (base_name, class_object.__tablename__)
            views.append(
                ModelView(
                    class_object,
                    db.session,
                    name=class_object.__tablename__,
                    category=base_name,
                    endpoint=name,
                )
            )

