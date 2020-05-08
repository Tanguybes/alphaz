import hmac
from hashlib import sha256
from flask import request, send_file, send_from_directory, safe_join, abort

from ..models.api.structures import AlphaFlask
from .apis import *

class Parameter():
    name = None
    value = None
    default = None
    cacheable = False
    required = False
    options = None

    def __init__(self,name,default=None,options=None,cacheable=True,required=False):
        self.name       = name
        self.default    = default
        self.cacheable  = cacheable
        self.options    = options
        self.required  = required

api = AlphaFlask(__name__)

# Specify the debug panels you want
#api.config['DEBUG_TB_PANELS'] = [ 'flask_debugtoolbar.panels.versions.VersionDebugPanel', 'flask_debugtoolbar.panels.timer.TimerDebugPanel', 'flask_debugtoolbar.panels.headers.HeaderDebugPanel', 'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel', 'flask_debugtoolbar.panels.template.TemplateDebugPanel', 'flask_debugtoolbar.panels.sqlalchemy.SQLAlchemyDebugPanel', 'flask_debugtoolbar.panels.logger.LoggingPanel', 'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel', 'flask_debugtoolbar_lineprofilerpanel.panels.LineProfilerPanel' ]
#toolbar = flask_debugtoolbar.DebugToolbarExtension(api)

def route(path,parameters=[],parameters_names=[],methods = ['GET'],cache=False,logged=False,admin=False,timeout=None):
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
            api.info('{:4} {}'.format(request.method,request.path))

            missing = False

            dataPost                = request.get_json()

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
                api.access_denied()   
                return api.get_return(return_status=401)
            elif logged and not api.get_logged_user():
                api.access_denied() 
                return api.get_return(return_status=401)

            if admin and not api.check_is_admin():
                api.access_denied() 
                return api.get_return(return_status=401)

            reloadCache         = request.args.get('reloadCache', None) is not None or api.is_time(timeout)
            
            api.configure_route(path,parameters=parameters,cache=cache)
            if api.keep(path,parameters) and not reloadCache: 
                api.get_cached(path,parameters)
            else:
                api.init_return()
                if not missing:
                    func(*args, **kwargs)
                else:
                    api.set_error('inputs')
                api.cache(path,parameters)
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


@route('/test',
parameters=[Parameter('name')])
def api_test():
    name = api.get('name')
    api.print("Hello to you %s !"%name)
    
@route('/register', methods = ['POST'],
    parameters = [
        Parameter('mail',required=True),
        Parameter('username',required=True),
        Parameter('password',required=True),
        Parameter('password_confirmation',required=True),
    ])
def register():
    if api.get_logged_user() is not None:
        return api.set_error('logged')

    db    = api.get_database('users')

    api_users.try_register_user(
        api,
        db,
        api.get('mail'), 
        api.get('username'), 
        api.get('password'), 
        api.get('password_confirmation'))

@route('/register/validation',methods = ['GET'],
    parameters  = [
        Parameter('tmp_token',required=True)
    ],
    parameters_names=[])
def register_validation():
    if api.get_logged_user() is not None:
        return api.set_error('logged')

    db             = api.get_database('users')
    api_users.confirm_user_registration(api,token   = api.get('tmp_token'),db=db)

# LOGIN
@route('/auth', methods = ['POST'],
    parameters  = [
        Parameter('username',required=True),
        Parameter('password',required=True)
    ])
def login():
    db     = api.get_database('users')
    api_users.try_login(api, db, api.get('username'), api.get('password'), request.remote_addr)

@route('/password/lost', methods = ['POST'],
    parameters = [
        Parameter('username',required=False),
        Parameter('mail',required=False)
    ])
def password_lost():
    if api.get_logged_user() is not None:
        return api.set_error('logged')

    username    = api.get('username')
    mail        = api.get('mail')

    if username is not None or mail is not None:
        db                 = api.get_database('users')
        username_or_mail    = username if mail is None else mail
        print('here',username_or_mail)
        api_users.ask_password_reset(api,username_or_mail,db=db) 
    else:
        api.set_error('inputs')

@route('/password/reset', methods = ['GET', 'POST'],
    parameters  = [
        Parameter('tmp_token',required=True),
        Parameter('password',required=True),
        Parameter('password_confirmation',required=True)
    ])
def password_reset_validation():
    if api.get_logged_user() is not None:
        return api.set_error('logged')

    db     = api.get_connection('users')
    api_users.confirm_user_password_reset(api,token=api.get('tmp_token'), password=api.get('password'), password_confirmation=api.get('password_confirmation'),db=db)

@route('/logout',cache=False,logged=False,methods = ['GET', 'POST'],
    parameters  = [],  parameters_names=[])
def logout():
    token   = api.get_token()
    db     = api.get_connection('users')

    api_users.logout(api,token,db=db)

@route('/profile/password', logged=True, methods = ['POST'],
    parameters  = [
        Parameter('password',required=True),
        Parameter('password_confirmation',required=True)
    ])
def reset_password():
    user_data               = api.get_logged_user()

    db     = api.get_connection('users')
    api_users.try_reset_password(api,user_data, api.get('password'), api.get('password_confirmation'),db=db,log=api.log)
    
##################################################################################################################
# MAILS
##################################################################################################################

@route('/mails/mailme',logged=False,cache=False)
def mail_me():
    db         = api.get_connection('users')
    print('mailme')
    api_mails.mail_me(api,db,close_cnx=True)

@route('/mails/stayintouch',logged=False,cache=False, 
    parameters = [
        Parameter('token',required=True),
        Parameter('mail',required=True),
        Parameter('name',required=True)
    ])
def mails_stay_in_touch():
    token           = api.get('token')
    user_mail       = api.get('mail')
    name            = api.get('name')

    #db             = db.get_survey_connection()
    db             = api.get_connection('users')
    api_mails.stay_in_touch(api,user_mail,name, token,db)

@route('/mails/requestview',logged=False,cache=False, 
    parameters = [
        Parameter('token',required=True),
        Parameter('mail',required=True),
        Parameter('name',required=True),
        Parameter('id',required=True)
    ])
def mails_request_view():
    token       = api.get('token')
    user_mail   = api.get('mail')
    mail_type   = api.get('name')
    mail_id     = api.get('id')

    db             = api.get_connection('users')
    api_mails.request_view(api,user_mail,token,mail_type,mail_id,db,close_cnx=True)

@route('/mails/unsubscribe',logged=False,cache=False, 
    parameters = [
        Parameter('token',required=True),
        Parameter('mail',required=True),
        Parameter('type',required=True)
    ])
def mails_unsubscribe():
    token       = api.get('token')
    user_mail   = api.get('mail')
    mail_type   = api.get('type')

    db             = api.get_connection('users')
    api_mails.request_unsubscribe(api,user_mail,token,mail_type,db,close_cnx=True)

@route('/admin/logs/clear', methods = ['GET'], admin=True,
    parameters = [

    ])
def clear_logs():
    done = api_logs.clear_logs(api)
    if not done:
        api.set_error('database')

@route('/admin/logs', methods = ['POST', 'GET'],admin=True,
    parameters = [
        Parameter('page',required=True),
        Parameter('startDate',required=True),
        Parameter('endDate',required=True)
    ])
def admin_logs():
    page = int(api.get('page'))
    limit = True
    if page == 0: limit = False
    start_date  = api.get('startDate') 
    end_date    = api.get('endDate')

    data = api_logs.get_logs(api,start_date=start_date, end_date=end_date, useLimit=limit, pageForLimit=page)
    api.set_data(data)