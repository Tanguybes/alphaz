from sqlalchemy import Table, Column, ForeignKey, Integer, String, Text, DateTime, UniqueConstraint
from sqlalchemy.types import TypeDecorator

from core import core

db = core.get_database()
ma = core.ma

def repr(instance):
    columns_values  = {x:instance.__dict__[x] if x in instance.__dict__ else None for x,y in instance.columns.items() if y['show']}
    text            = ','.join("%s=%s"%(x,y) for x,y in columns_values.items())
    return '<%s %r>'%(instance.__tablename__.capitalize(),text)

class AlphaColumn(Column):
    show = True

class AlphaTable(object):
    schema = None

    """@declared_attr
    def __tablename__(self):
        return self.__name__.lower()

    def get_table_name(self):
        return self.__name__.lower()"""

    def __repr__(self): return repr(self) 

    @classmethod
    def get_schema(class_obj):
        if class_obj.schema is not None:
            return class_obj.schema

        schema_name = type(class_obj).__name__ + 'Schema'
        
        #instance    = class_obj.__dict__['_sa_instance_state'].__dict__['class_']
        columns     = [k for k,v in class_obj.__dict__.items() if hasattr(v,'show')]

        class_obj.schema = type(schema_name, (ma.Schema,),
            {
                'Meta':type('Meta', (object,),{'fields':columns})
            }
        )
        return class_obj.schema

class AlphaTableId(AlphaTable):
    id =  AlphaColumn(Integer, primary_key=True, autoincrement=True)

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

"""def set_alpha_tables(db):
    engine  = db.get_engine()
    AlphaTable.prepare(engine)
    #engine  = db.get_engine(bind="users")
    #AlphaTable.prepare(engine, reflect=True)
    pass"""

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