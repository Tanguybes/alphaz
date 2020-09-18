from ...utils.api import route, Parameter

from ...libs import logs_lib, flask_lib

from ...models.main import AlphaException

from core import core

api         = core.api
db          = core.db
log         = core.get_logger('api')

category = 'database'

def get_table_and_database(schema:str,table:str):
    db              = core.get_database(schema)
    if db is None:
        raise AlphaException('cannot_find_schema',parameters={'schema':schema})

    if not schema in flask_lib.TABLES:
        raise AlphaException('schema_not_loaded',parameters={'schema':schema})

    """if table in flask_lib.TABLES:
        obj = flask_lib.TABLES[table]
        obj.__table__.drop()
        api.set_data("%s dropped"%table)"""

    if not table in flask_lib.TABLES[schema]:
        raise AlphaException('cannot_find_table',parameters={'table':table})

    table_object = flask_lib.TABLES[schema][table]
    
    """if not table in db.metadata.tables:
        raise AlphaException('cannot_find_table',parameters={'table':table})

    table_object = db.metadata.tables[table]"""
    return table_object, db

@route('/database/tables',category=category)
def liste_tables():
    api.set_data({x:list(y.metadata.tables.keys()) for x,y in core.databases.items()})

@route('/database/create',category=category,
    parameters=[
        Parameter('schema',required=True),
        Parameter('table',required=True)
    ]
)
def create_table():
    table_object, db    = get_table_and_database(api.get('schema'), api.get('table'))
    table_object.__table__.create(db.engine)

@route('/database/drop',category=category,
    parameters=[
        Parameter('schema',required=True),
        Parameter('table',required=True)
    ]
)
def drop_table():
    table_object, db    = get_table_and_database(api.get('schema'), api.get('table'))
    table_object.__table__.drop(db.engine)
    
    """if not table in db.metadata.tables:
        raise AlphaException('cannot_find_table',parameters={'table':table})

    table_object = db.metadata.tables[table]

    table_object.__table__.drop()
    api.set_data("%s dropped"%table)"""