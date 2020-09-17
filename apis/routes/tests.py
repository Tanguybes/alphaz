from ...utils.api import route, Parameter

from .. import tests

from ...libs import test_lib

from core import core

api         = core.api
db          = core.db
log         = core.get_logger('api')

category    = 'tests'

@route('/tests',category=category,parameters=
[
    Parameter('category',ptype=str),
    Parameter('group',ptype=str),
    Parameter('name',ptype=str),
    Parameter('test',ptype=bool)
])
def get_tests():
    tests = test_lib.get_tests_auto(
        core.config.get('directories/tests'),
        category=api.get('category'),
        group=api.get('group'),
        name=api.get('name'),
        test=api.get('test')
    )
    api.set_data(tests)

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