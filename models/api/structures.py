import os, configparser, datetime, copy

from flask import Flask
from flask import jsonify, request
from flask_mail import Mail

from ...libs import mail_lib
from ...utils.logger import AlphaLogger
from ...utils.apis import api_users
from ...config.config import AlphaConfig

from .utils import CustomJSONEncoder

SEPARATOR = '::'
pattern_mail = '{{%s}}'

def fill_config(configuration,source_configuration):
    for key, value in configuration.items():
        for key2, value2 in source_configuration.items():
            if type(value) != dict and pattern_mail%key2 in str(value):
                value = str(value).replace(pattern_mail%key2,value2)
        configuration[key] = value

def merge_configuration(configuration,source_configuration,replace=False):
    new_configuration = {}
    for key2, value2 in source_configuration.items():
        if (not key2 in configuration or replace) and type(value2) != dict:
            configuration[key2] = value2

    """for key, value in configuration.items():
        print('key',key)
        if not key in new_configuration:
            new_configuration[key] = value
    return new_configuration"""

class AlphaFlask(Flask):
    mode            = 'data'
    message         = 'No message'
    data            = {}
    returned        = {}

    conf            = None
    config_path     = ''

    verbose         = False

    current_route   = None
    routes          = {}
    routes_values   = {}

    log = None

    connections     = {}

    def set_connection(self,name, cnx_fct):
        self.connections[name] = cnx_fct

    def get_connection(self,name):
        return self.connections[name]()

    def init(self,config_path):
        self.set_config(config_path)

        #api.debug                                   = False
        self.config['SECRET_KEY']                    = self.get_config('flask_key')
        self.config['JWT_SECRET_KEY']                = self.get_config('jwt_key')
        self.config['JSONIFY_PRETTYPRINT_REGULAR']   = False
        self.json_encoder                            = CustomJSONEncoder

        mail_config = self.get_config('mail_server')

        self.config.update(
            MAIL_USE_TLS    = mail_config['tls'],
            MAIL_USE_SSL    = mail_config['ssl'],
            MAIL_SERVER     = mail_config['server'],
            MAIL_PORT       = mail_config['port'],
            MAIL_USERNAME   = mail_config['mail'],
            MAIL_PASSWORD   = mail_config['password']
        )
        self.mail = Mail(self)

    def start(self,debug=False):
        pid                 = os.getpid()     
        self.conf.set_data(paths=['tmp','process'],value=pid)
        self.conf.save()

        ssl_context = None
        if self.conf.get('ssl'):
            ssl_context = (self.conf.get('ssl_cert'),self.conf.get('ssl_key'))

        host        = self.conf.get('host')
        port        = self.conf.get('port')
        threaded    = self.conf.get('threaded')

        root_log    = self.get_config('log_directory')
        self.log    = AlphaLogger('api','api',root=root_log)

        self.log.info('Run api on host %s port %s '%(host,port))

        self.run(host=host,port=port,debug=debug,threaded=threaded,ssl_context=ssl_context)

    def stop(self,config_path=None):
        if config_path is None:
            config_path = self.config_path
        if self.config_path is None:
            return

        self.set_config(config_path=config_path)

        pid = self.get_config(['tmp','process'])

        os.kill(pid, 9)

        print('Process n°%s killed'%pid)

    def set_config(self,config_path):
        self.config_path    = config_path
        self.conf           = AlphaConfig(filepath=config_path) # root=os.path.dirname(os.path.realpath(__file__))

    def get_config(self,name=''):
        return self.conf.get(name)

    def get_url(self):
        return self.get_config('host_public')

    def set_data(self, data):
        self.mode       = 'data'
        self.data       = data

    def get_cached(self,api_route,parameters=[]):
        key = self.getKey(api_route,parameters)
        if self.verbose:
            print('   GET cache for %s'%api_route)
        if key in self.routes_values:
            self.returned, self.data = self.routes_values[key]
        else:
            self.set_error('No cache')

    def get_return(self,forceData=False, return_status=None):
        self.returned['data'] = {}
        if len(self.data) > 0 or forceData:
            self.returned['data'] = self.data
        
        response = jsonify(self.returned)
        if return_status is not None:
            response.status_code = return_status
        return response

    def init_return(self):
        returned = {'token_status' : 'success', 'status' : 'success', 'error':0}
        self.returned, self.data = returned, {}

    def print(self,message):
        self.mode       = 'print'
        self.message    = message

    def set_error(self,message):
        self.returned['status']     = message
        self.returned['error']      = 1

    def set_status(self,status):
        self.returned['status'] = status
        
    def access_denied(self):
        self.returned['token_status'] = 'denied'
        self.returned['error']      = 1

    def get_last_request_time(self):
        return None if self.current_route is None else self.current_route.lasttime

    def debug_parameters(self):
        if self.current_route is not None:
            self.current_route.debugParameters()

    def get(self,name):
        if self.current_route is None:
            return None
        parameter = self.current_route.get(name)
        return None if parameter is None else parameter.value

    def configure_route(self,api_route,parameters,cache=False):
        self.routes[api_route]   = Route(api_route,parameters,cache=cache)
        self.current_route       = self.routes[api_route]

    def getRoute(self,api_route):
        if not api_route in self.routes:
            return None
        return self.routes[api_route]

    def keep(self,api_route,parameters=[]):
        route = self.getRoute(api_route)
        if not route.cache:
            if self.verbose:
                print('Api %s not cacheable'%api_route)
            return False
        key             = self.getKey(api_route,parameters)
        return_cache    = key in self.routes_values.keys()
        return return_cache

    def cache(self,api_route,parameters=[]):
        self.current_route.lasttime     = datetime.datetime.now()
        key                             = self.getKey(api_route,parameters)
        if self.verbose:
            print('   SET new cache for %s (last run = %s)'%(api_route,datetime.datetime.now()))

        self.routes_values[key] = (self.returned, self.data)
        return self.routes_values[key]

    def getKey(self,api_route,parameters=[]):
        key =  '%s%s'%(api_route, SEPARATOR)
        for parameter in parameters:
            if parameter.cacheable:
                key += '%s=%s;'%(parameter.name,parameter.value)
        return key

    def error(self,message):
        if self.log is not None:
            self.log.error(message)

    def get_logged_user(self):
        user_data   = None
        token       = self.get_token()
        if token is not None:
            cnx         = self.get_connection('users')
            user_data   = api_users.get_user_dataFromToken(self,cnx,token)
        return user_data

    def get_token(self):
        token = None
        # Get token from authorization bearer
        auth = request.headers.get("Authorization", None)
        if auth is not None:
            if 'bearer' in auth.lower():
                parts = auth.split()
                if len(parts) > 1:
                    token = parts[1]

        # Token from get have priority if present
        token_from_get = request.args.get('token', None)
        if token_from_get is not None:
            token =  token_from_get

        # Token from post
        dataPost                = request.get_json()
        if 'token' in dataPost:
            token = dataPost['token']
        return token

    def check_is_admin(self):
        user_data = self.get_logged_user()
        if user_data is not None:
            if user_data['role'] >= 9:
                return True
        return False

    def isTime(self,timeout, verbose=False):
        isTime = False
        if timeout is not None:
            now     = datetime.datetime.now()
            lastrun = self.get_last_request_time()
            nextrun = lastrun + datetime.timedelta(minutes=timeout)
            isTime  = now > nextrun

            if verbose:
                print('Time: ',isTime, ' now=',now,', lastrun=',lastrun,' nextrun=',nextrun)
        return isTime

    def send_mail(self,mail_config,parameters_list,cnx,log,sender=None,close_cnx=True):
        mail_type       = mail_config['mail_type']

        sender = self.get_config('mail_sender')
        if mail_config['sender'] is not None:
            sender              = mail_config['sender']
        
        full_parameters_list = []
        for parameters in parameters_list:
            root_configuration          = copy.deepcopy(self.get_config())
            parameters_config           = copy.deepcopy(mail_config['parameters'])

            full_parameters = {}

            fill_config(parameters_config,source_configuration=parameters)
            fill_config(root_configuration,source_configuration=parameters)
            fill_config(root_configuration,source_configuration=parameters_config)
            fill_config(parameters_config,source_configuration=root_configuration)
            fill_config(parameters,source_configuration=parameters_config)
            fill_config(parameters,source_configuration=root_configuration)

            merge_configuration(full_parameters, source_configuration=root_configuration,replace=True)
            merge_configuration(full_parameters, source_configuration=parameters_config,replace=True)
            merge_configuration(full_parameters, source_configuration=parameters,replace=True)

            full_parameters_list.append(full_parameters)
            """for key, value in full_parameters.items():
                print('     {:20} {}'.format(key,value))
            exit()"""
        
        valid = mail_lib.send_mail(
            host_web=self.get_config('host_web'),
            mail_path=self.get_config('mail_path'),
            mail_type=mail_type,
            parameters_list=full_parameters_list,
            sender=sender,
            cnx=cnx,
            log=log,
            key_signature = self.get_config('mail_key_signature'),
            close_cnx=close_cnx
        )
        if not valid:
            self.set_error('mail_error')

class Route:
    cache           = False
    route           = ""
    parameters      = {}
    lasttime        = datetime.datetime.now()

    def __init__(self, route, parameters, cache=False):
        self.route = route
        self.cache = cache
        self.parameters = {y.name:y for y in parameters}

    def get(self,name):
        if name in self.parameters:
            return self.parameters[name]
        return None

    def debugParameters(self):
        print('    > ',self.route)
        for name, parameter in self.parameters.items():
            print('    {:10} {:10} {:10}'.format(name,str(parameter.default),str(parameter.value)))
