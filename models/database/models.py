import datetime
from sqlalchemy import (
    Table,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    DateTime,
    UniqueConstraint,
    event
)
from sqlalchemy.types import TypeDecorator

from ...libs import flask_lib

from .utils import get_schema


def repr(instance):
    columns_values = {
        x: instance.__dict__[x] if x in instance.__dict__ else None
        for x, y in instance.columns.items()
        if y["show"]
    }
    text = ",".join("%s=%s" % (x, y) for x, y in columns_values.items())
    return "<%s %r>" % (instance.__tablename__.capitalize(), text)


class AlphaColumn(Column):
    show = True


class AlphaTable(object):
    # def __new__(class_, *args, **kwargs):
    #    return object.__new__(class_, *args, **kwargs)

    def __init__(self):
        self.schema = None
        self.ensure = False

    """@declared_attr
    def __tablename__(self):
        return self.__name__.lower()

    def get_table_name(self):
        return self.__name__.lower()"""

    def __repr__(self):
        return repr(self)

    @classmethod
    def get_schema(class_obj):
        if hasattr(class_obj, "schema") and class_obj.schema is not None:
            return class_obj.schema
        return get_schema(class_obj)

    @staticmethod
    def set_attrib_listener(target, value, old_value, initiator):
        tg = target.__table__.c[initiator.key]
        python_type = tg.type.python_type
        if value is None:
            return None
        if python_type == datetime.datetime and type(value) == str:
            return datetime.datetime.strptime(value,"%Y-%m-%dT%H:%M:%S") if 'T' in value else datetime.datetime.strptime(value,"%Y-%m-%d %H:%M:%S")
        if python_type == datetime.datetime and type(value) == datetime.datetime:
            return value
        try:
            return python_type(value)
        except Exception as ex:
            raise

    @classmethod
    def __declare_last__(cls):
        for column in cls.__table__.columns.values():
            event.listen(
                getattr(cls, column.key),
                "set",
                cls.set_attrib_listener,
                retval=True,
            )

class AlphaTableId(AlphaTable):
    id = AlphaColumn(Integer, primary_key=True, autoincrement=True)


class AlphaTableUpdateDate(AlphaTable):
    update_date = AlphaColumn(
        DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now
    )


class AlphaTableIdUpdateDate(AlphaTableId):
    update_date = AlphaColumn(
        DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now
    )


class AlphaTableIdUpdateDateCreationDate(AlphaTableId):
    update_date = AlphaColumn(
        DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now
    )
    creation_date = AlphaColumn(DateTime, default=datetime.datetime.now)


class AlphaFloat(TypeDecorator):
    impl = String

    def process_literal_param(self, value, dialect):
        return str(float(value)) if value is not None else None

    process_bind_param = process_literal_param

    def process_result_value(self, value, dialect):
        return float(value) if value is not None else None


class AlphaInteger(TypeDecorator):
    impl = Integer

    def process_literal_param(self, value, dialect):
        return str(int(value)) if value is not None else None

    process_bind_param = process_literal_param

    def process_result_value(self, value, dialect):
        return float(int) if value is not None else None


"""
    
# creating class dynamically 
def get_model(db):
    models = {}
    
    name = "logs"
    models[name] = type(name.capitalize(), (db.Model, ), { 
        # constructor 
        "__tablename__": name, 
        "__repr__": repr,

        "columns": {
            'id':{"show":False},
            'type':{"show":True},
            'origin':{"show":True},
            'message':{"show":True},
            'stack':{"show":True},
            'date':{"show":True}
        },

        "id": db.Column(db.Integer, primary_key=True),
        "type": db.Column(db.String(30)),
        "origin": db.Column(db.String(30)),
        "message": db.Column(db.Text),
        "stack": db.Column(db.Text),
        "date": db.Column(db.DateTime)
    })

    return models
    """
