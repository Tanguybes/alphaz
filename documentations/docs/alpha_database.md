# Alpha database system

## Automatic structure

Compared to native SqlAlchemy in alpha you only need to instantiate the table model:

```py
from alphaz.models.database.models import AlphaTable, AlphaColumn
DB = core.db

class DuckType(DB.Model, AlphaTable):
    __bind_key__ = DB
    __tablename__= "duck_type"

    type_id = AlphaColumn(INTEGER, primary_key=True, autoincrement=True)
    name = AlphaColumn(TEXT,nullable = False, default = "SuperDuck")

class DuckMedal(DB.Model, AlphaTable):
    __bind_key__ = DB
    __tablename__= "duck_medal"

    name = AlphaColumn(TEXT,nullable = False, default = "Lucky")
    duck_id       = AlphaColumn(INTEGER, ForeignKey ('duck.duck_id'      ), nullable     = False, default= -1)

class Duck(DB.Model, AlphaTable):
    __bind_key__ = DB
    __tablename__= "duck"

    duck_id = AlphaColumn(INTEGER, primary_key=True, autoincrement=True, visible=False)
    name = AlphaColumn(TEXT,nullable = False, default = "")

    # Many to one
    duck_type_id = AlphaColumn(INTEGER, ForeignKey ('duck_type.type_id'), nullable = False, default = -1, visible=False)
    duck_type = relationship("DuckType")

    # One to many
    medals = relationship("DuckMedals")    
```

By default a select query on **Duck** class defined like this:

```py
master_duck = DuckType(ame="Master Duck")
DB.add(master_duck)

ducky = Duck(name="Ducky",duck_type=master_duck)
DB.add(ducky)

honnor_medal = DuckMedal(name="Honnor",duck_id=ducky.duck_id)
lucky_medal = DuckMedal(name="Lucky",duck_id=ducky.duck_id)
DB.add(ducky)

ducks = DB.select(Duck, filters=[Duck.name=="Ducky"], first=True)
```

Will result in this:

```json
{
    "duck_id":1,
    "name":"Ducky",
    "duck_type": {
        "type_id":1,
        "duck_type": "Master Duck"
    },
    "medals": [
        {"name":"Honnor"},
        {"name":"Lucky"}    
    ]
}
``` 

## Schema

!!! note
    The associated Schema is created automatically, with classic and nested fields.

However Marshmallow schema could be defined using the classic way [Marshmallow](https://marshmallow.readthedocs.io/en/stable/index.html):

- Set visible to **False** if you dont want the column to appears in the Schema.

!!! important 
    Schema must be defined after the Model

```py
DB = core.db

class DuckTypeSchema(Schema):
    type_id = fields.Integer()
    name = fields.String()

class DuckMedalSchema(Schema):
    name = fields.String()

class DuckSchema(Schema):
    name = fields.String()

    # Many to One
    duck_type = fields.Nested(DuckTypeSchema)

    # One to many
    medals = fields.List(fields.Nested(DuckMedalSchema))
```

!!! important
    **Alpha** will automatically detect the schema if the name is defined as ```"{ModelName}Schema"``` and is located in the same file.

!!! note 
    In this mode, Schema could be defined automatically, excepted for nested fields.

### Specific Schema

Schema could be specified for every request:

```py
DB.select(model  = Duck, schema = DuckSchema)
```