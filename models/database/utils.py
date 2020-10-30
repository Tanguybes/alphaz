

def get_schema(class_obj):
    from core import core
    schema_name = type(class_obj).__name__ + 'Schema'
    
    #instance    = class_obj.__dict__['_sa_instance_state'].__dict__['class_']
    columns     = [k for k,v in class_obj.__dict__.items() if hasattr(v, 'show')]

    class_obj.schema = type(schema_name, (core.ma.Schema,),
        {
            'Meta':type('Meta', (object,),{'fields':columns})
        }
    )
    return class_obj.schema