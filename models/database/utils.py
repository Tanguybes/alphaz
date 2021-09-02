from marshmallow import Schema, fields
from marshmallow_sqlalchemy import ModelConverter

def __get_nested_schema(mapper):
    from core import core
    mapper_name = str(mapper).split('class ')[1].split('->')[0]
    schema_name = mapper_name + 'Schema'

    columns = []
    if hasattr(mapper,'columns'):
        for column in mapper.columns:
            columns.append(column.name)

    # Dynamic schema class creation
    properties = {
        'Meta':type('Meta', (object,),{'fields':columns})
    }
    schema = type(schema_name, (core.ma.Schema,),
        properties
    )
    return schema

def get_schema(class_obj):
    columns, nested, = [], {}
    for key, value in class_obj.__dict__.items():
        if key.startswith('__'): continue
        if not hasattr(value, "is_attribute") or not value.is_attribute: continue
        
        if hasattr(value, 'visible') and getattr(value, 'visible'):
            columns.append(key)
        elif hasattr(value,"entity"):
            nested[key] = __get_nested_schema(value.entity) 

    g_s = ModelConverter()
    flds = {x:y for x,y in g_s.fields_for_model(class_obj).items() if x in columns}

    for key, value in nested.items():
        flds[key] = fields.Nested(value)

    generated_schema = Schema.from_dict(flds)
    class_obj.schema = generated_schema

    return class_obj.schema