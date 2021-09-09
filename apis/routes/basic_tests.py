import uuid

from ...utils.api import route, Parameter

from .. import tests

from core import core

api         = core.api

@route('/test/parameters',cache=True,timeout=100,
    parameters=[Parameter('value'), Parameter('options',options=['Y','N'])]
)
def api_test():
    parameters = api.get_parameters()
    parameters['uuid'] = uuid.uuid4()
    return parameters
    
@route('/test/insert',)
def test_insert():
    return tests.insert()

@route('/test/html',
    parameters=[Parameter('message')]
)
def html_message():
    return api.set_html('hello.html',parameters={"message":api.get('message')})