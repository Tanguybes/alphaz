import os, configparser, datetime, copy, jwt, logging, re, itertools, sys, importlib, warnings

from flask import Flask, jsonify, request, Response, make_response
from flask_mail import Mail

with warnings.catch_warnings():
     from flask_marshmallow import Marshmallow
     
from flask_statistics import Statistics
from flask_debugtoolbar import DebugToolbarExtension
from flask_admin import Admin

from gevent.pywsgi import WSGIServer
from werkzeug.debug import DebuggedApplication

import flask_monitoringdashboard

from ...libs import mail_lib, flask_lib, io_lib, converter_lib, os_lib, json_lib

from ...models.logger import AlphaLogger
from ...models.main import AlphaException
from ...models.config import AlphaConfig
from ...models.json import AlphaJSONEncoder

from ...utils.time import tic, tac

from . import _utils, _colorations

SEPARATOR = '::'

def check_format(data,depth=3):
   if depth == 0: return True

   accepted = [int,str,float]
   if type(data) in accepted: return True

   if type(data) == list and len(data) != 0:
        return check_format(data[0],depth-1)
   if type(data) == dict and len(data) != 0:
        return check_format(list(data.keys())[0],depth-1) & check_format(list(data.values())[0],depth-1)
   return False
class AlphaFlask(Flask):

    def __init__(self,*args,no_log:bool=False,**kwargs):
        super().__init__(*args,**kwargs)

        # Get werkzueg logger
        log = logging.getLogger('werkzeug')
        log.addFilter(_colorations.WerkzeugColorFilter()) #TODO: set in configuration
        log.disabled        = no_log

        self.pid            = None
        self.html           = {'page':None,'parameters':None}

        self.user           = None
        self.mode           = 'data'
        self.message        = 'No message'
        self.data           = {}
        self.returned       = {}

        self.conf           = None
        self.config_path    = ''

        self.current_route  = None
        self.routes         = {}
        self.routes_values  = {}

        self.dataPost       = {}
        self.dataGet        = {}

        self.log            = None
        self.db             = None

        self.admin_db       = None
        self.ma             = None

        self.file_to_get   = (None, None)
        self.file_to_set    = (None, None)

        # need to put it here to avoid warnings
        self.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True #TODO modify

        self.ma = Marshmallow(self)

    def reset(self):
        self.data = {}
        self.returned = {}
        self.dataGet = {}

    def set_databases(self,db_cnx):
        if not 'main' in db_cnx:
            self.log.error('You must define a <main> database')
            exit()

        uri = db_cnx['main']['cnx']
        if ':///' in uri:
            io_lib.ensure_file(uri.split(':///')[1])
        db_type = db_cnx['main']['type']
        self.config['SQLALCHEMY_DATABASE_URI'] = uri

        for key, cf_db in db_cnx.items():
            self.config['SQLALCHEMY_BINDS'] = {x:y['cnx'] for x,y in db_cnx.items()}

        #self.api.config['MYSQL_DATABASE_CHARSET']           = 'utf8mb4'
        #self.api.config['QLALCHEMY_TRACK_MODIFICATIONS']    = True
        #self.api.config['EXPLAIN_TEMPLATE_LOADING']         = True
        self.config['UPLOAD_FOLDER']                    = self.root_path

    def init(self,encode_rules={}):
        #from core import core

        routes = self.conf.get("routes")
        if routes is None:
            self.log.error('Missing <routes> parameters in api configuration')
        else:
            for route in routes:
                module = importlib.import_module(route)

        # check request
        # ! freeze - dont know why
        """db              = core.get_database('main')
        request_model    = database_lib.get_table('main', 'request')
        try:
            self.log.debug('Check <request> table')
            obj = db.exist(request_model)
        except:
            self.log.info('Creating <request> table')
            request_model.__table__.create(db.engine)"""

        # Flask configuration
        # todo: check JWT_SECRET_KEY: mandatory
        confs = self.conf.get('config')
        if confs is not None:
            for key, value in confs.items():
                self.config[key] = value

        self.json_encoder = AlphaJSONEncoder
        for key_rule, fct in encode_rules.items():
            AlphaJSONEncoder.rules[key_rule] = fct

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

        toolbar = self.conf.get('toolbar')
        if toolbar:
            toolbar = DebugToolbarExtension(self)

        #config_dashboard = os.path.join(self.root,'apis','config.cfg')

        #flask_monitoringdashboard.config.init_from(file=config_dashboard)
        monitoring = self.conf.get('monitoring')
        if monitoring:
            flask_monitoringdashboard.bind(self)

        if self.conf.get('admin_databases'):
            self.init_admin_view()

        #Base.prepare(self.db.engine, reflect=True)

    def set_config(self,name,configuration=None,root=None):
        self.log.debug('Set <%s> configuration for API from %s in %s'%(configuration,name,root))
        self.config_path    = root + os.sep + name + '.json'
        self.configuration  = configuration

        self.conf           = AlphaConfig(name=name,
            configuration=configuration,
            root=root,
            log=self.log
        ) # root=os.path.dirname(os.path.realpath(__file__))
        
        if self.conf.get('routes_no_log'):
            _colorations.WerkzeugColorFilter.routes_exceptions = self.conf.get('routes_no_log')

    def init_admin_view(self):
        views               = flask_lib.load_views(self.log)
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
        mode        = self.conf.get('mode')

        if self.debug:
            sys.dont_write_bytecode = True

        self.log.info('Run api on host %s port %s %s'%(host,port,'DEBUG MODE' if self.debug else ''))

        #try:
        if mode == "wsgi":
            self.log.info("Running %sWSGI mode"%("debug " if self.debug else ""))
            application = DebuggedApplication(self, True) if self.debug else self

            if host == "0.0.0.0" or host == "localhost" and os_lib.is_linux():
                host = ""
            server = WSGIServer((host, port), application)
            server.serve_forever()
        else:
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
        self.mode       = 'set_file'
        self.file_to_set       = (directory, filename)

    def get_file(self,directory, filename,attached=False):
        self.mode       = 'get_file' if not attached else 'get_file_attached'
        self.file_to_get       = (directory, filename)

    def set_html(self,page,parameters={}):
        self.mode = 'html'
        self.html = {'page':page,'parameters':parameters}

    def get_cached(self,api_route,parameters=[]):
        key = self.get_key(api_route,parameters)
        if self.log:
            self.log.info('   GET cache for %s'%api_route)
        if key in self.routes_values:
            self.returned, self.data = self.routes_values[key]
        else:
            self.set_error('No cache')

    def get_return(self,forceData=False, return_status=None):
        self.returned['data'] = {}
        
        data = {} if self.data is None else self.data

        # Convert
        self.returned['data'] = data
        if not check_format(data):
            self.returned['data'] = json_lib.jsonify_data(data)

        format_ = 'json'
        if 'format' in self.dataGet:
            format_ = self.dataGet['format'].lower()

        """if 'output' in self.dataGet:
            data = {}
            data['columns'] = self.returned['data']
            data."""

        if 'xml' in format_:
            xml_output = converter_lib.dict_to_xml(self.returned,attr_type=not 'no_type' in format_)                                              
            response = make_response(xml_output)                                           
            response.headers['Content-Type'] = 'text/xml; charset=utf-8'            
            return response
        else:
            returned = self.returned # jsonify(self.returned)
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
        self.file_to_get = (None, None)
        self.file_to_set = (None, None)
        self.returned, self.data = returned, {}

    def print(self,message):
        self.mode       = 'print'
        self.message    = message

    def set_error(self,message):
        self.mode       = 'data'
        description = message
        if type(message) == AlphaException:
            description = message.description 
            message     = message.name
            self.log.error(message + ' - ' + description,level=2)
            
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
        self.returned['token']       = jwt.encode(
            {
                'username': user_data['username'], 
                'id': user_data['id'], 
                'time': str(datetime.datetime.now())
            }, 
            api.config['JWT_SECRET_KEY'], algorithm='HS256').decode('utf-8')
        self.returned['valid_until'] = datetime.datetime.now() + datetime.timedelta(days=7)

    def get_last_request_time(self):
        return None if self.current_route is None else self.current_route.lasttime

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
            return False
        key             = self.get_key(api_route,parameters)
        return_cache    = key in self.routes_values.keys()
        return return_cache

    def cache(self,api_route,parameters=[]):
        self.current_route.lasttime     = datetime.datetime.now()
        key                             = self.get_key(api_route,parameters)
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
            from ...apis import users #todo: modify
            from core import core
            db = core.get_database('users')
            user_data   = users.get_user_dataFromToken(self,db,token)
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
        admin = False
        user_data = self.get_logged_user()
        if user_data is not None:
            if user_data['role'] >= 9:
                admin = True
        if not admin:
            ip = request.remote_addr
            if self.conf.get('admins') and ip in self.conf.get('admins'):
                admin = True
        return admin

    def is_time(self,timeout):
        is_time = False
        if timeout is not None:
            now         = datetime.datetime.now()
            lastrun     = self.get_last_request_time()
            nextrun     = lastrun + datetime.timedelta(minutes=timeout)
            is_time     = now > nextrun
        return is_time

    def send_mail(self,mail_config,parameters_list,db,sender=None):
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
        
        mail_lib.KEY_SIGNATURE = self.get_config('mails/key_signature'),
        valid = mail_lib.send_mail(
            mail_path       = self.get_config('mails/path'),
            mail_type       = config['mail_type'],
            parameters_list = full_parameters_list,
            sender          = sender,
            db              = db,
            log             = self.log
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
