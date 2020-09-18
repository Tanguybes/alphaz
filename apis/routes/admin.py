import inspect

from ...utils.api import route, Parameter

from ...libs import logs_lib, flask_lib

from ...models.main import AlphaException

from core import core

api         = core.api
db          = core.db
log         = core.get_logger('api')

category    = "admin"

@route('/admin/logs/clear',category=category, methods = ['GET'], admin=True,
    parameters = [

    ])
def clear_logs():
    done = logs_lib.clear_logs(api)
    if not done:
        api.set_error('database')

@route('/admin/logs',category=category, methods = ['POST', 'GET'],admin=True,
    parameters = [
        Parameter('page',required=True,ptype=int),
        Parameter('startDate',required=True),
        Parameter('endDate',required=True)
    ])
def admin_logs():
    page        = int(api.get('page'))
    limit = True
    if page == 0: limit = False

    data = logs_lib.get_logs(start_date=api.get('startDate'), end_date=api.get('endDate'), useLimit=limit, pageForLimit=page)
    api.set_data(data)