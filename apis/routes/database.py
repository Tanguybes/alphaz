from ...utils.api import route, Parameter

from ...libs import logs_lib, flask_lib, database_lib

from ...models.main import AlphaException

from core import core

api         = core.api
db          = core.db
log         = core.get_logger('api')

@route('/database/tables',admin=True)
def liste_tables():
    api.set_data(database_lib.get_databases_tables_dict())

@route('/database/create',admin=True,
    parameters=[
        Parameter('schema',required=True),
        Parameter('table',required=True)
    ]
)
def create_table():
    created = core.create_table(api.get('schema'), api.get('table'))
    if created:
        api.set_data('table %s created'%api.get('table'))

@route('/database/drop',admin=True,
    parameters=[
        Parameter('schema',required=True),
        Parameter('table',required=True)
    ]
)
def drop_table():
    dropped = core.drop_table(api.get('schema'), api.get('table'))
    if dropped:
        api.set_data('table %s dropped'%api.get('table'))

@route('/database/init', admin=True,
parameters=[
    Parameter('database',required=True),
    Parameter('table',required=True),
    Parameter('drop',ptype=bool)
])
def init_database():
    log = core.get_logger('database')
    database_lib.init_databases(api.get('database'),api.get('table'),drop=api.get('drop'),log=log)

@route('/database/init/all', admin=True,
parameters=[
    Parameter('database',required=True),
    Parameter('drop',ptype=bool)
])
def init_all_database():
    log = core.get_logger('database')

    databases = database_lib.get_databases_tables_dict()
    if not api.get('database') in databases:
        raise AlphaException('missing_database',parameters={'database':api.get('database')})

    for table in databases[api.get('database')]:
        database_lib.init_databases(api.get('database'),table,drop=api.get('drop'),log=log)