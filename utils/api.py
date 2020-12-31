import traceback
from flask import request, send_file, send_from_directory, safe_join, abort, url_for, render_template

from ..models.main import AlphaException
from ..models.api import Parameter

from core import core
api = core.api
db  = core.db
log = core.get_logger('api')

ROUTES = {}

# Specify the debug panels you want
#api.config['DEBUG_TB_PANELS'] = [ 'flask_debugtoolbar.panels.versions.VersionDebugPanel', 'flask_debugtoolbar.panels.timer.TimerDebugPanel', 'flask_debugtoolbar.panels.headers.HeaderDebugPanel', 'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel', 'flask_debugtoolbar.panels.template.TemplateDebugPanel', 'flask_debugtoolbar.panels.sqlalchemy.SQLAlchemyDebugPanel', 'flask_debugtoolbar.panels.logger.LoggingPanel', 'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel', 'flask_debugtoolbar_lineprofilerpanel.panels.LineProfilerPanel' ]
#toolbar = flask_debugtoolbar.DebugToolbarExtension(api)

def route(path, 
        parameters=None, 
        methods = ['GET'], 
        cache=False,
        logged=False,
        admin=False,
        timeout=None,
        category=None
        ):
    if path[0] != '/': path = '/' + path

    """if not 'parameters' in locals() or parameters is None:
        parameters = []"""
    if parameters is None: parameters = []
    for i, parameter in enumerate(parameters):
        if type(parameter) == str:
            parameters[i] = Parameter(parameter)

    def api_in(func):
        @api.route(path, methods = methods, endpoint=func.__name__)
        def api_wrapper(*args,**kwargs):
            if path not in ["/", "/status"]:
                log.debug('get api route {:10} with method <{}>'.format(path,func.__name__))

            if not api.configure_route(path, parameters=parameters, cache=cache, logged=logged, admin=admin, timeout=timeout):
                return api.get_current_route().get_return()

            route = api.get_current_route()
            if not route.keep(): 
                route.init_return()
                try:
                    output = func(*args, **kwargs)
                    if output == 'timeout':
                        api.timeout()
                    elif output is not None:
                        api.set_data(output)
                except Exception as ex:
                    if api.get("error_format") and api.get("error_format").lower() == "exception":
                        raise ex
                    if 'alpha' in str(type(ex)).lower():
                        api.set_error(ex)
                    else:
                        raise ex
                route.set_cache()
            else:
                api.get_cached()

            return route.get_return()

        api_wrapper.__name__ = func.__name__

        if cache:
            parameters.append(Parameter('reset_cache',ptype=bool,cacheable=False))

        if not 'category' in locals() or category is None:
            category = func.__module__.split('.')[-1]
        else:
            category = category.lower()
            
        kwargs_ = {
            "path":path,
            "parameters":parameters,
            "parameters_names":[x.name for x in parameters],
            "methods":methods,
            "cache":cache,
            "logged":logged,
            "admin":admin,
            "timeout":timeout,
            "category": category
        }
        api_wrapper._kwargs   = kwargs_

        paths  = [ x for x in path.split('/') if x.strip() != '']
        if len(paths) == 1:
            paths = ['root',paths[0]]

        arguments = {x:y if x != 'parameters' else [j.__dict__ for j in y] for x,y in kwargs_.items()}

        trace = traceback.format_stack()

        ROUTES[path] = {
            'category': category,
            'name': func.__name__,
            'module': '',
            'paths':paths,
            'arguments':arguments
        }

        return api_wrapper
    return api_in

##################################################################################################################
# BASE API FUNCTIONS
##################################################################################################################

@api.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Origin,Accept,X-Requested-With,Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    #response.headers.set('Allow', 'GET, PUT, POST, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response