from flask import request, send_file, send_from_directory, safe_join, abort, url_for, render_template

from ..models.database import main_definitions as defs

from core import core
api = core.api
db  = core.db
log = core.get_logger('api')

class Parameter():
    def __init__(self,name,default=None,options=None,cacheable=True,required=False,ptype=str):
        self.name       = name
        self.default    = default
        self.cacheable  = cacheable
        self.options    = options
        self.required   = required
        self.type       = str(ptype).replace("<class '","").replace("'>","")

# Specify the debug panels you want
#api.config['DEBUG_TB_PANELS'] = [ 'flask_debugtoolbar.panels.versions.VersionDebugPanel', 'flask_debugtoolbar.panels.timer.TimerDebugPanel', 'flask_debugtoolbar.panels.headers.HeaderDebugPanel', 'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel', 'flask_debugtoolbar.panels.template.TemplateDebugPanel', 'flask_debugtoolbar.panels.sqlalchemy.SQLAlchemyDebugPanel', 'flask_debugtoolbar.panels.logger.LoggingPanel', 'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel', 'flask_debugtoolbar_lineprofilerpanel.panels.LineProfilerPanel' ]
#toolbar = flask_debugtoolbar.DebugToolbarExtension(api)

def route(path,parameters=[],parameters_names=[],methods = ['GET'],cache=False,logged=False,admin=False,timeout=None,category='main'):
    if path[0] != '/': path = '/' + path
    def api_in(func):
        names = []
        for parameter in parameters:
            if not parameter.name in names:
                names.append(parameter.name)
            if parameter.name in parameters_names:
                parameters_names.remove(parameter.name)
        for name in parameters_names:
            parameters.append(Parameter(name))

        @api.route(path, methods = methods, endpoint=func.__name__)
        def api_wrapper(*args,**kwargs):
            api.dataGet = {} if request.args is None else {x:y for x,y in request.args.items()}

            if logged:
                api.user            = api.get_logged_user()

            if len(request.path.strip()) > 1:
                api.info('{:4} {}'.format(request.method,request.path))

            missing = False

            dataPost                = request.get_json()
            api.dataPost            = {} if dataPost is None else {x:y for x,y in dataPost.items()}

            if 'format' in api.dataGet:
                api.format = api.dataGet['format'].lower()

            """if api.debug:
                print('POST:',dataPost)
                print('GET:',request.args)
                print('JSON:',request.get_json())
                print('VALUES:',request.values)
                print('PARAMETERS',parameters)"""

            for parameter in parameters:
                parameter.value         = request.args.get(parameter.name,parameter.default)
                if parameter.value is None and dataPost is not None and parameter.name in dataPost:
                    parameter.value     = dataPost[parameter.name]

                if parameter.options is not None and parameter.value not in parameter.options:
                    parameter.value = None
                if parameter.required and parameter.value is None:
                    missing = True
                    api.error('Missing parameter %s'%parameter.name)

            token           = api.get_token()
            if logged and token is None:
                print('   Empty token')
                api.access_denied()   
                return api.get_return(return_status=401)
            elif logged and (api.user is None or len(api.user) == 0):
                print('   Wrong user',api.user)
                api.access_denied() 
                return api.get_return(return_status=401)

            if admin and not api.check_is_admin():
                print('   Not admin')
                api.access_denied() 
                return api.get_return(return_status=401)

            api.configure_route(path,parameters=parameters,cache=cache)
            reset_cache = request.args.get('reset_cache', None) is not None or api.is_time(timeout)

            if api.keep(path,parameters) and not reset_cache: 
                api.get_cached(path,parameters)
            else:
                api.init_return()
                if not missing:
                    func(*args, **kwargs)
                else:
                    api.set_error('inputs')
                api.cache(path,parameters)

            if api.mode == 'html':
                return render_template(api.html['page'],**api.html['parameters'])
            if api.mode == 'print':
                return api.message
            if api.mode == 'file':
                file_path, filename = api.file_to_send
                if file_path is not None and filename is not None:
                    api.info('Sending file %s from %s'%(filename,file_path))
                    try:
                        return send_from_directory(file_path, filename=filename, as_attachment=True)
                    except FileNotFoundError:
                        abort(404)
                else:
                    api.set_error('missing_file')

            return api.get_return()
        api_wrapper.__name__ = func.__name__

        if cache:
            parameters.append(Parameter('reset_cache',ptype=bool,cacheable=False))

        api_wrapper._kwargs   = {
            "path":path,
            "parameters":parameters,
            "parameters_names":parameters_names,
            "methods":methods,
            "cache":cache,
            "logged":logged,
            "admin":admin,
            "timeout":timeout,
            "category":category.lower()
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