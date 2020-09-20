import os, configparser, datetime, copy, jwt, logging, re, itertools, sys, importlib

from dicttoxml import dicttoxml

from flask import Flask, jsonify, request, Response, make_response
from flask_mail import Mail
from flask_marshmallow import Marshmallow
from flask_statistics import Statistics
from flask_debugtoolbar import DebugToolbarExtension
from flask_admin import Admin    
import flask_monitoringdashboard

from ...libs import mail_lib, flask_lib, io_lib
from ...utils.logger import AlphaLogger
from ...models.main import AlphaException
from ...config.config import AlphaConfig

from . import _converters, _utils, _colorations

SEPARATOR = '::'

class AlphaFlask(Flask):

    def __init__(self,*args,no_log:bool=False,**kwargs):
        super().__init__(*args,**kwargs)

        # Get werkzueg logger
        log = logging.getLogger('werkzeug')
        log.addFilter(_colorations.WerkzeugColorFilter())
        log.disabled        = no_log

        self.pid            = None
        self.format         = 'json'
        self.html           = {'page':None,'parameters':None}

        self.user           = None
        self.mode           = 'data'
        self.message        = 'No message'
        self.data           = {}
        self.returned       = {}

        self.conf           = None
        self.config_path    = ''

        self.verbose        = False

        self.current_route  = None
        self.routes         = {}
        self.routes_values  = {}

        self.dataPost       = {}
        self.dataGet        = {}

        self.log            = None
        self.db             = None
        self.statistics     = None

        self.admin_db       = None
        self.ma             = None

        self.file_to_send   = (None, None)

        # need to put it here to avoid warnings
        self.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True #TODO modify

        self.ma = Marshmallow(self)

    def init(self,encode_rules={}):
        from core import core
        self.log: AlphaLogger    = core.get_logger('api')

        self.set_config('api',core.configuration)

        routes = self.conf.get('routes')
        if routes is None:
            self.log.error('Missing <routes> parameters in api configuration')
        else:
            for route in routes:
                importlib.import_module(route)

        self.db = core.db

        # Flask configuration
        confs = self.conf.get('config')
        if confs is not None:
            for key, value in confs.items():
                self.config[key] = value

        self.json_encoder = _converters.AlphaJSONEncoder
        for key_rule, fct in encode_rules.items():
            _converters.AlphaJSONEncoder.rules[key_rule] = fct

        self.config['SECRET_KEY'] = b'_5#y2L"F4Q8z\n\xec]/'

        """self.debug = self.conf.get('debug')
        if self.debug:
            self.info('Debug mode activated')"""

        # MAILS
        mail_config = self.get_config('mails/mail_server')

        if mail_config is not None:
            self.config.update(
                MAIL_USE_TLS    = mail_config['tls'],
                MAIL_USE_SSL    = mail_config['ssl'],
                MAIL_SERVER     = mail_config['server'],
                MAIL_PORT       = mail_config['port'],
                MAIL_USERNAME   = mail_config['mail'],
                MAIL_PASSWORD   = mail_config['password']
            )
            self.mail = Mail(self)
        else:
            self.log.error('Mail configuration is not defined ("mails/mail_server" parameter)') 

        toolbar = DebugToolbarExtension(self)

        #config_dashboard = os.path.join(self.root,'apis','config.cfg')

        #flask_monitoringdashboard.config.init_from(file=config_dashboard)
        flask_monitoringdashboard.bind(self)

        from ..database.main_definitions import Request
        if core.db is None:
            self.log.error('Cannot initiate statistics, db is None')
        self.statistics = Statistics(self, core.db, Request)

        if self.conf.get('admin_databases'):
            self.init_admin_view()

        #Base.prepare(self.db.engine, reflect=True)

    def init_admin_view(self):
        models_sources      = self.conf.get('models') or []

        models_sources.append("alphaz.models.database.main_definitions")
        modules             = flask_lib.get_definitions_modules(models_sources,log=self.log)

        views               = list(itertools.chain(*[flask_lib.load_views(module=x) for x in modules]))
        endpoints           = [x.endpoint for x in views]

        from ..database.views import views as alpha_views
        for view in alpha_views:
            if view.endpoint not in endpoints:
                views.append(view)

        self.admin_db       = Admin(self, name=self.get_config('name'), template_mode='bootstrap3')
        
        self.admin_db.add_views(*views)

    def start(self):
        if self.pid is not None:
            return
            
        self.pid                 = os.getpid()     
        #self.conf.set_data(paths=['tmp','process'],value=pid)
        #self.conf.save()

        ssl_context = None
        if self.conf.get('ssl'):
            ssl_context = (self.conf.get('ssl_cert'),self.conf.get('ssl_key'))

        host        = self.conf.get('host')
        port        = self.conf.get('port')
        threaded    = self.conf.get('threaded')
        self.debug  = self.conf.get('debug')

        if self.debug:
            sys.dont_write_bytecode = True

        self.log.info('Run api on host %s port %s %s'%(host,port,'DEBUG MODE' if self.debug else ''))

        #try:
        self.run(host=host,port=port,debug=self.debug,threaded=threaded,ssl_context=ssl_context)
        #except SystemExit:
        #    self.info('API stopped')

    def stop(self,config_path=None):
        if config_path is None:
            config_path = self.config_path
        if self.config_path is None:
            return

        self.set_config(config_path=config_path,configuration=self.configuration)

        pid = self.get_config(['tmp','process'])

        os.kill(pid, 9)

        self.log.info('Process n°%s killed'%pid)

    def set_config(self,config_path,configuration=None,root=None):
        self.config_path    = config_path
        self.configuration  = configuration
        self.conf           = AlphaConfig(filepath=config_path,configuration=configuration,root=root,log=self.log) # root=os.path.dirname(os.path.realpath(__file__))

    def get_database(self,name):
        return self.conf.get_database(name)

    def get_config(self,name=''):
        if '/' in name:
            name = name.split('/')
        conf = self.conf.get(name)
        return conf

    def get_url(self):
        ssl     = self.get_config('ssl')
        pref    = 'https://' if ssl else 'http://'
        return pref + self.get_config('host_public')

    def set_data(self, data):
        self.mode       = 'data'
        self.data       = data

    def set_file(self,directory, filename):
        self.mode       = 'file'
        self.file_to_send       = (directory, filename)

    def set_html(self,page,parameters={}):
        self.mode = 'html'
        self.html = {'page':page,'parameters':parameters}

    def get_cached(self,api_route,parameters=[]):
        key = self.get_key(api_route,parameters)
        if self.verbose:
            print('   GET cache for %s'%api_route)
        if key in self.routes_values:
            self.returned, self.data = self.routes_values[key]
        else:
            self.set_error('No cache')

    def get_return(self,forceData=False, return_status=None):
        self.returned['data'] = {}
        
        if self.data is not None:
        #if self.data is not None and (len(self.data) > 0 or forceData):
            self.returned['data'] = self.data
    
        self.returned['data'] = _converters.jsonify_data(self.returned['data'])

        if self.format == 'xml':
            xml_output = dicttoxml(self.returned)                                              
            response = make_response(xml_output)                                           
            response.headers['Content-Type'] = 'text/xml; charset=utf-8'            
            return response
        else:
            returned = jsonify(self.returned)
            if return_status is not None:
                returned.status_code = return_status

        return returned

    """def get_return(self,forceData=False, return_status=None):
        self.returned['data'] = {}
        if self.data is not None and (len(self.data) > 0 or forceData):
            self.returned['data'] = self.data
        
        response = jsonify(self.returned)
        if return_status is not None:
            response.status_code = return_status
        return response"""

    def init_return(self):
        returned = {'token_status' : 'success', 'status' : 'success', 'error':0}
        self.file_to_send = (None, None)
        self.returned, self.data = returned, {}

    def print(self,message):
        self.mode       = 'print'
        self.message    = message

    def set_error(self,message):
        description = message
        if type(message) == AlphaException:
            description = message.description 
            message     = message.name
            
        self.returned['status']                 = message
        self.returned['status_description']     = description
        self.returned['error']                  = 1

    def set_status(self,status):
        self.returned['status'] = status

    def timeout(self):
        self.returned['status'] = 'timeout'
        
    def access_denied(self):
        self.returned['token_status'] = 'denied'
        self.returned['error']      = 1

    def log_user(self,user_data):
        self.returned['role']        = 'user'
        if user_data['role'] >= 9:
            self.returned['role']    = 'admin'
        self.returned['token']       = jwt.encode({'username': user_data['username'], 'id': user_data['id'], 'time': str(datetime.datetime.now())}, api.config['JWT_SECRET_KEY'], algorithm='HS256').decode('utf-8')
        self.returned['valid_until'] = datetime.datetime.now() + datetime.timedelta(days=7)

    def get_last_request_time(self):
        return None if self.current_route is None else self.current_route.lasttime

    def debug_parameters(self):
        if self.current_route is not None:
            self.current_route.debugParameters()

    def get(self,name):
        if self.current_route is None:
            return None
        parameter = self.current_route.get(name)
        value = None if parameter is None else parameter.value
        if str(value) == 'false': return False
        if str(value) == 'true': return True
        return value

    def configure_route(self,api_route,parameters,cache=False):
        self.routes[api_route]   = Route(api_route,parameters,cache=cache)
        self.current_route       = self.routes[api_route]

    def get_route(self,api_route):
        if not api_route in self.routes:
            return None
        return self.routes[api_route]

    def keep(self,api_route,parameters=[]):
        route = self.get_route(api_route)
        if not route.cache:
            if self.verbose:
                print('Api %s not cacheable'%api_route)
            return False
        key             = self.get_key(api_route,parameters)
        return_cache    = key in self.routes_values.keys()
        return return_cache

    def cache(self,api_route,parameters=[]):
        self.current_route.lasttime     = datetime.datetime.now()
        key                             = self.get_key(api_route,parameters)
        if self.verbose:
            print('   SET new cache for %s (last run = %s)'%(api_route,datetime.datetime.now()))

        self.routes_values[key] = (self.returned, self.data)
        return self.routes_values[key]

    def get_key(self,api_route,parameters=[]):
        key =  '%s%s'%(api_route, SEPARATOR)
        for parameter in parameters:
            if parameter.cacheable:
                key += '%s=%s;'%(parameter.name,parameter.value)
        return key

    def error(self,message):
        if self.log is not None:
            self.log.error(message,level=4)

    def info(self,message):
        if self.log is not None:
            self.log.info(message,level=4)

    def get_logged_user(self):
        user_data   = None
        token       = self.get_token()
        if token is not None:
            from ...utils.apis import api_users #todo: modify
            from core import core
            db = core.get_database('users')
            user_data   = api_users.get_user_dataFromToken(self,db,token)
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
        if dataPost is not None and 'token' in dataPost:
            token = dataPost['token']
        return token

    def check_is_admin(self):
        user_data = self.get_logged_user()
        if user_data is not None:
            if user_data['role'] >= 9:
                return True
        return False

    def is_time(self,timeout, verbose=False):
        is_time = False
        if timeout is not None:
            now         = datetime.datetime.now()
            lastrun     = self.get_last_request_time()
            nextrun     = lastrun + datetime.timedelta(minutes=timeout)
            is_time     = now > nextrun

            if verbose:
                print('Time: ',is_time, ' now=',now,', lastrun=',lastrun,' nextrun=',nextrun)
        return is_time

    def send_mail(self,mail_config,parameters_list,db,sender=None,close_cnx=True):
        # Configuration
        main_mail_config    = self.get_config(['mails'])
        config              = self.get_config(['mails',"configurations",mail_config])
        if config is None or type(config) != dict:
            self.log.error('Missing "%s" mail configuration in "%s"'%(config,self.config_path))
            return False

        # Parameters
        root_config = copy.copy(main_mail_config['parameters'])
        for key, parameter in main_mail_config['parameters'].items():
            root_config[key] = parameter

        # Sender
        if sender is None:
            if 'sender' in config:
                sender              = config['sender']
            elif 'sender' in main_mail_config:
                sender              = main_mail_config['sender']
            elif 'sender' in main_mail_config['parameters']:
                sender              = main_mail_config['parameters']['sender']
            else:
                self.set_error('sender_error')
                return False
        
        full_parameters_list = []
        for parameters in parameters_list:
            #root_configuration          = copy.deepcopy(self.get_config())

            parameters_config = {}
            if 'parameters' in config:
                parameters_config           = copy.deepcopy(config['parameters'])

            full_parameters = {'title':config['title']}

            _utils.fill_config(parameters_config,source_configuration=parameters)
            _utils.fill_config(root_config,source_configuration=parameters)
            _utils.fill_config(root_config,source_configuration=parameters_config)
            _utils.fill_config(parameters_config,source_configuration=root_config)
            _utils.fill_config(parameters,source_configuration=parameters_config)
            _utils.fill_config(parameters,source_configuration=root_config)

            _utils.merge_configuration(full_parameters, source_configuration=root_config,replace=True)
            _utils.merge_configuration(full_parameters, source_configuration=parameters_config,replace=True)
            _utils.merge_configuration(full_parameters, source_configuration=parameters,replace=True)

            full_parameters_list.append(full_parameters)
            """for key, value in full_parameters.items():
                print('     {:20} {}'.format(key,value))
            exit()"""
        
        mail_lib.KEY_SIGNATURE = self.get_config('mails/key_signature'),
        valid = mail_lib.send_mail(
            mail_path       = self.get_config('mails/path'),
            mail_type       = config['mail_type'],
            parameters_list = full_parameters_list,
            sender          = sender,
            db              = db,
            log             = self.log,
            close_cnx       = close_cnx
        )
        if not valid:
            self.set_error('mail_error')
        return valid

class Route:
    def __init__(self, route, parameters, cache=False):
        self.route = route
        self.cache = cache
        self.parameters = {y.name:y for y in parameters}
        self.lasttime        = datetime.datetime.now()

    def get(self,name):
        if name in self.parameters:
            return self.parameters[name]
        return None

    def debugParameters(self):
        for name, parameter in self.parameters.items():
            print('    {:10} {:10} {:10}'.format(name,str(parameter.default),str(parameter.value)))
