import importlib
from marshmallow import Schema
from marshmallow import fields as cfields
from marshmallow_sqlalchemy import ModelConverter, fields

def __get_nested_schema(mapper, parent=None):
    #return get_schema(mapper.entity, parent=parent)

    auto_schema = get_auto_schema(mapper.entity)

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
    return auto_schema

def get_auto_schema(model):    
    from core import core

    properties = {
        'Meta':type('Meta', (object,),
        {
            'model':model,
            'include_fk':True,
            "load_instance":True,
            "include_relationships":True
        })
    }
    schema = type(f"{model.__name__}Schema", (core.ma.SQLAlchemyAutoSchema,),
        properties
    )
    return schema

SCHEMAS = {}

def get_schema(class_obj, parent=None):
    """ Get Schema for a model

    Args:
        class_obj ([type]): [description]
        parent ([type], optional): [description]. Defaults to None.

    Returns:
        [type]: [description]
    """
    # custom Schema declaration
    module_name = class_obj.__module__
    mod = importlib.import_module(module_name)
    schema_name = f"{class_obj.__name__}Schema"
    if hasattr(mod, schema_name):
        return getattr(mod, schema_name)

    auto_schema = get_auto_schema(class_obj)

    cols, related, related_list = {}, {}, {}
    for key, value in auto_schema._declared_fields.items():
        if type(value) == fields.Related:
            related[key] = value
        elif type(value) == fields.RelatedList:
            related_list[key] = value
        else:
            cols[key] = cols

    columns, nesteds, list_nesteds = [], {}, {}
    for key, value in class_obj.__dict__.items():
        if key.startswith('__'): continue
        if not hasattr(value, "is_attribute") or not value.is_attribute: continue
        
        if hasattr(value, 'visible') and getattr(value, 'visible'):
            columns.append(key)
        elif hasattr(value,"entity"):
            columns.append(key)
            if parent is None or not class_obj in SCHEMAS:
                nested_schema = __get_nested_schema(value.entity, parent=class_obj)
                #nested_schema = get_schema(value.entity.entity)
            else:
                nested_schema = SCHEMAS[class_obj]

            if key in related:
                nesteds[key] = nested_schema
            elif key in related_list:
                list_nesteds[key] = nested_schema

    #g_s = ModelConverter()
    #flds = {x:y for x,y in g_s.fields_for_model(class_obj).items() if x in columns}

    for key, value in nesteds.items():
        cols[key] = fields.Nested(value)
    for key, value in list_nesteds.items():
        cols[key] = cfields.List(fields.Nested(value))

    generated_schema = Schema.from_dict(cols)
    class_obj.schema = generated_schema
    SCHEMAS[class_obj] = generated_schema
    return class_obj.schema