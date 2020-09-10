import datetime

from flask import request

from ...utils.api import route, Parameter
from ..main import get_routes_infos

from core import core
api = core.api
db  = core.db
log = core.get_logger('api')

@route('/')
def home():
    config = api.conf
    #statistics = api.statistics

    api.set_html('home.html',parameters={
        'mode':core.config.configuration,
        'mode_color': '#e74c3c' if core.config.configuration == 'prod' else ('#0270D7' if core.config.configuration == 'dev' else '#2ecc71'),
        'title':config.get('templates/home/title'),
        'description':config.get('templates/home/description'),
        'year':datetime.datetime.now().year,
        'users':0,
        'ip': request.environ['REMOTE_ADDR'],
        'admin': core.config.configuration == 'local',
        'routes': get_routes_infos(log=log),
        'compagny': config.get('parameters/compagny'),
        'compagny_website': config.get('parameters/compagny_website'),
        'statistics': core.config.configuration == 'local'
    })