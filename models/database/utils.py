from marshmallow import Schema, fields

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
    from core import core
    mapper_name = str(class_obj.__mapper__).split('class ')[1].split('->')[0]
    #schema_name = type(class_obj).__name__ + 'Schema'
    schema_name = mapper_name + 'Schema'

    #instance    = class_obj.__dict__['_sa_instance_state'].__dict__['class_']
    columns, nested = [], {}
    for key, value in class_obj.__dict__.items():
        if key.startswith('__'): continue
        if not hasattr(value,"is_attribute") or not value.is_attribute: continue
        if hasattr(value, 'show'):
            columns.append(key)

        elif hasattr(value,"entity"):
            nested[key] = __get_nested_schema(value.entity) 

    # Dynamic schema class creation
    properties = {
        'Meta':type('Meta', (object,), {'fields':columns})
    }
    for key, value in nested.items():
        properties[key] = fields.Nested(value)

    class_obj.schema = type(schema_name, (core.ma.Schema,),
        properties
    )
    return class_obj.schema