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
    mandatory = False
    options = None

    def __init__(self,name,default=None,options=None,cacheable=True,mandatory=False):
        self.name       = name
        self.default    = default
        self.cacheable  = cacheable
        self.options    = options
        self.mandatory  = mandatory

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

            if api.debug:
                print('POST:',dataPost)
                print('GET:',request.args)
                print('JSON:',request.get_json())
                print('VALUES:',request.values)
                print('PARAMETERS',parameters)

            for parameter in parameters:
                parameter.value         = request.args.get(parameter.name,parameter.default)
                if parameter.value is None and dataPost is not None and parameter.name in dataPost:
                    parameter.value     = dataPost[parameter.name]

                if parameter.options is not None and parameter.value not in parameter.options:
                    parameter.value = None
                if parameter.mandatory and parameter.value is None:
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

            reloadCache         = request.args.get('reloadCache', None) is not None or api.isTime(timeout)
            
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
        Parameter('mail',mandatory=True),
        Parameter('username',mandatory=True),
        Parameter('password',mandatory=True),
        Parameter('password_confirmation',mandatory=True),
    ])
def register():
    if api.get_logged_user() is not None:
        return api.set_error('logged')

    cnx    = api.get_connection('users')

    api_users.try_register_user(
        api,
        cnx,
        api.get('mail'), 
        api.get('username'), 
        api.get('password'), 
        api.get('password_confirmation'))

@route('/register/validation',methods = ['GET'],
    parameters  = [
        Parameter('tmp_token',mandatory=True)
    ],
    parameters_names=[])
def register_validation():
    if api.get_logged_user() is not None:
        return api.set_error('logged')

    cnx             = api.get_connection('users')
    api_users.confirm_user_registration(api,token   = api.get('tmp_token'),cnx=cnx)

# LOGIN
@route('/auth', methods = ['POST'],
    parameters  = [
        Parameter('username',mandatory=True),
        Parameter('password',mandatory=True)
    ])
def login():
    cnx     = api.get_connection('users')
    api_users.try_login(api, cnx, api.get('username'), api.get('password'), request.remote_addr)

@route('/password/lost', methods = ['GET', 'POST'],
    parameters = [
        Parameter('username',mandatory=False),
        Parameter('mail',mandatory=False)
    ])
def password_lost():
    if api.get_logged_user() is not None:
        return api.set_error('logged')

    username    = api.get('username')
    mail        = api.get('mail')

    if username is not None or mail is not None:
        cnx                 = api.get_connection('users')
        username_or_mail    = username if mail is None else mail

        api_users.ask_password_reset(api,username_or_mail,cnx=cnx) 
    else:
        api.set_error('inputs')

@route('/password/reset', methods = ['GET', 'POST'],
    parameters  = [
        Parameter('tmp_token',mandatory=True),
        Parameter('password',mandatory=True),
        Parameter('password_confirmation',mandatory=True)
    ])
def password_reset_validation():
    if api.get_logged_user() is not None:
        return api.set_error('logged')

    cnx     = api.get_connection('users')
    api_users.confirm_user_password_reset(api,token=api.get('tmp_token'), password=api.get('password'), password_confirmation=api.get('password_confirmation'),cnx=cnx)

@route('/logout',cache=False,logged=True,methods = ['GET', 'POST'],
    parameters  = [],  parameters_names=[])
def logout():
    token   = api.get_token()
    cnx     = api.get_connection('users')

    api_users.logout(api,token,cnx=cnx)

@route('/profile/password', logged=True, methods = ['POST'],
    parameters  = [
        Parameter('password',mandatory=True),
        Parameter('password_confirmation',mandatory=True)
    ])
def reset_password():
    user_data               = api.get_logged_user()

    cnx     = api.get_connection('users')
    api_users.try_reset_password(api,user_data, api.get('password'), api.get('password_confirmation'),cnx=cnx,log=api.log)
    
##################################################################################################################
# MAILS
##################################################################################################################

@route('/mails/mailme',logged=False,cache=False)
def mail_me():
    cnx         = api.get_connection('users')
    print('mailme')
    api_mails.mail_me(api,cnx,close_cnx=True)

@route('/mails/stayintouch',logged=False,cache=False, 
    parameters = [
        Parameter('token',mandatory=True),
        Parameter('mail',mandatory=True),
        Parameter('name',mandatory=True)
    ])
def mails_stay_in_touch():
    token           = api.get('token')
    user_mail       = api.get('mail')
    name            = api.get('name')

    #cnx             = cnx.get_survey_connection()
    cnx             = api.get_connection('users')
    api_mails.stay_in_touch(api,user_mail,name, token,cnx)

@route('/mails/requestview',logged=False,cache=False, 
    parameters = [
        Parameter('token',mandatory=True),
        Parameter('mail',mandatory=True),
        Parameter('name',mandatory=True),
        Parameter('id',mandatory=True)
    ])
def mails_request_view():
    token       = api.get('token')
    user_mail   = api.get('mail')
    mail_type   = api.get('name')
    mail_id     = api.get('id')

    api_mails.request_view(api,user_mail,token,mail_type,mail_id,cnx,close_cnx=True)

@route('/mails/unsubscribe',logged=False,cache=False, 
    parameters = [
        Parameter('token',mandatory=True),
        Parameter('mail',mandatory=True),
        Parameter('type',mandatory=True)
    ])
def mails_unsubscribe():
    token       = api.get('token')
    user_mail   = api.get('mail')
    mail_type   = api.get('type')

    cnx             = api.get_connection('users')
    api_mails.request_unsubscribe(api,user_mail,token,mail_type,cnx,close_cnx=True)

# COINBASE
@route('/coinbase', methods = ['GET', 'POST'])
def coinbase():
    cnx             = api.get_connection('users')
    secret          = '665e62d1-8a4e-4ca8-ae7a-a52eef626493'
    request_data    = request.data.decode('utf-8')
    request_sig     = request.headers.get('X-CC-Webhook-Signature', None)
    dataPost        = request.get_json()
    if dataPost is not None and request_sig is not None:
        mac = hmac.new(secret.encode('utf-8'),
                    msg=request_data.encode('utf-8'),
                    digestmod=sha256)
        hex_comparative = mac.hexdigest()
        if hex_comparative != request_sig:
            return api.set_error('wrong_sig')

        mail = "undefined"
        # Check for transaction confirmation
        confirmed = False
        transaction = False
        transaction_name = "undefined"
        if 'event' in dataPost:
            event = dataPost['event']
            if 'type' in event:
                if 'confirmed' in event['type'] or 'failed' in event['type']:
                    confirmed = True
                if 'data' in event:
                    data = event['data']
                    if 'name' in data:
                        transaction_name = data['name']
                    if 'timeline' in data:
                        for element in data['timeline']:
                            if element['status'] == 'COMPLETED':
                                transaction = True
                            if element['status'] == 'UNRESOLVED':
                                # We should also accept underpaid, within some limit...
                                if element['context'] == 'UNDERPAID':
                                    if 'payments' in data:
                                        if 'CONFIRMED' in data['payments']['status']:
                                            if data['payments']['value']['local']['currency']['EUR']:
                                                value = data['payments']['value']['local']['amount']
                    if 'metadata' in data:
                        if 'email' in data['metadata']:
                            mail = data['metadata']

            if not confirmed or not transaction:
                return api.set_error('inputs')

            # update_coinbase_user(mail, nb_days, role_target)
            if transaction_name == 'Golliath - 1 Month':
                api_users.try_subscribe_user(api,mail, 30, 1,cnx,close_cnx=True)
            elif 'Test' in transaction_name:
                api_users.try_subscribe_user(api,mail, 30, 1,cnx,close_cnx=True)
            elif transaction_name == 'The Sovereign Individual':
                api_users.try_subscribe_user(api,'hourtane.axel@gmail.com', 30, 1,cnx,close_cnx=True)
            else:
                return api.set_error('unknowned_transaction')