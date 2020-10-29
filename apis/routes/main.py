import datetime

from flask import request, send_from_directory

from ...libs import test_lib, database_lib, api_lib
from ...utils.api import route, Parameter
from ...utils.time import tic, tac

from core import core
api = core.api
db  = core.db
LOG = core.get_logger('api')

@api.route('/assets/<path:path>')
def send_js(path):
    return send_from_directory('assets', filename=path)

@api.route('/images/<path:path>')
def send_images(path):
    return send_from_directory('images', filename=path)

@route('/page', parameters=[
    Parameter('page', required=True, ptype=str)
])
def index():
    api.set_html(api.get('page'))

@route('/profil/pic',logged=True)
def get_profil_pic():
    file_path = core.config.get('directories/images')
    api.get_file(file_path,api.get_logged_user()['id'])

@route('/files/upload',logged=True,methods=['POST'])
def upload_file():
    from flask import request
    uploaded_file = request.files['file']
    ext = uploaded_file.filename.split('.')[1]
    # str(filename) + '.' +
    filename = str(    api.get_logged_user()['id']) + '.' + ext

    file_path = core.config.get('directories/images')
    print('uploaded file to',file_path)
    api.set_file(file_path,filename)

@route('status')
def status():
    api.set_data(True)
    
@route('/')
def home():
    config = api.conf

    debug =  core.config.configuration != 'prod'

    tests = None
    try:
        tests = test_lib.get_tests_auto(core.config.get('directories/tests'))
    except Exception as ex:
        LOG.error(ex)

    parameters = {
        'mode':core.config.configuration,
        'mode_color': '#e74c3c' if core.config.configuration == 'prod' else ('#0270D7' if core.config.configuration == 'dev' else '#2ecc71'),
        'title':config.get('templates/home/title'),
        'description':config.get('templates/home/description'),
        'year':datetime.datetime.now().year,
        'users':0,
        'ip': request.environ['REMOTE_ADDR'],
        'admin': config.get('admin_databases'),
        'routes': api_lib.get_routes_infos(log=LOG),
        'compagny': config.get('parameters/compagny'),
        'compagny_website': config.get('parameters/compagny_website'),
        'dashboard':debug,
        'tests':tests,
        'databases':database_lib.get_databases_tables_dict()
    }
    api.set_html('home.html', parameters=parameters)
