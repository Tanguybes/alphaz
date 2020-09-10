from ...utils.api import route, Parameter

from .. import tests

from core import core

api         = core.api
db          = core.db
log         = core.get_logger('api')

category    = 'tests'

@route('/test',category=category,cache=True,timeout=100,
    parameters=[Parameter('value'),Parameter('options',options=['Y','N'])]
)
def api_test():
    api.set_data({
        'value':api.get('value'),
        'options':api.get('options')
    })
    
@route('/test/insert',category=category)
def test_insert():
    api.set_data(tests.insert())

@route('/test/html',category=category,
    parameters=[Parameter('message')]
)
def html_message():
    return api.set_html('hello.html',parameters={"message":api.get('message')})