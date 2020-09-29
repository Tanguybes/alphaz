import datetime

from flask import request, send_from_directory

from ...libs import test_lib, database_lib
from ...utils.api import route, Parameter
from ..main import get_routes_infos

from core import core
api = core.api
db  = core.db
log = core.get_logger('api')

@api.route('/assets/<path:path>')
def send_js(path):
    return send_from_directory('assets', filename=path)

@api.route('/images/<path:path>')
def send_images(path):
    return send_from_directory('images', filename=path)

@route('/page', parameters = [
    Parameter('page',required=True,ptype=str)
])
def index():
    api.set_html(api.get('page'))

@route('status')
def status():
    api.set_data(True)

@route('/')
def home():
    config = api.conf

    debug =  core.config.configuration != 'prod'

    parameters = {
        'mode':core.config.configuration,
        'mode_color': '#e74c3c' if core.config.configuration == 'prod' else ('#0270D7' if core.config.configuration == 'dev' else '#2ecc71'),
        'title':config.get('templates/home/title'),
        'description':config.get('templates/home/description'),
        'year':datetime.datetime.now().year,
        'users':0,
        'ip': request.environ['REMOTE_ADDR'],
        'admin': config.get('admin_databases'),
        'routes': get_routes_infos(log=log),
        'compagny': config.get('parameters/compagny'),
        'compagny_website': config.get('parameters/compagny_website'),
        'statistics': debug,
        'dashboard':debug,
        'tests':test_lib.get_tests_auto(core.config.get('directories/tests')),
        'databases':database_lib.get_databases_tables_dict()
    }
    api.set_html('home.html',parameters=parameters)