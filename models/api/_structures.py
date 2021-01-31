import os, configparser, datetime, copy, jwt, logging, re, itertools, sys, importlib, warnings
import traceback
from typing import Dict, List
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

from ...libs import (
    mail_lib,
    flask_lib,
    io_lib,
    converter_lib,
    os_lib,
    json_lib,
    config_lib,
    secure_lib,
)

from ...models.logger import AlphaLogger
from ...models.main import AlphaException
from ...models.config import AlphaConfig
from ...models.json import AlphaJSONEncoder

from ...utils.time import tic, tac

from . import _utils, _colorations

from ._route import Route
from ._parameter import Parameter

class AlphaFlask(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pid = None
        self.conf = None
        self.config_path = ""

        self.log = None
        self.log_requests = None
        self.db = None
        self.admin_db = None

        self.cache_dir = ""

        # need to put it here to avoid warnings
        #self.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True  # TODO modify

        self.ma = Marshmallow(self)

        self.routes_objects = {} 

    def get_parameters(self) -> Dict[str, object]:
        """Get non private route parameters values as a dict.

        Returns:
            Dict[str, object]: [description]
        """
        route = self.get_current_route()
        parameters = route.parameters
        parameters_values = {x: y.value for x, y in parameters.items() if not y.private}
        return parameters_values

    def set_data(self, data):
        self.get_current_route().set_data(data)

    def set_file(self, directory, filename):
        self.get_current_route().set_file(directory, filename)

    def get_file(self, directory, filename, attached=False):
        self.get_current_route().get_file(directory, filename, attached)

    def set_html(self, page, parameters={}):
        self.get_current_route().set_html(page, parameters)

    def set_databases(self, db_cnx):
        if not "main" in db_cnx:
            self.log.error("You must define a <main> database")
            exit()

        uri = db_cnx["main"]["cnx"]
        if ":///" in uri:
            io_lib.ensure_file(uri.split(":///")[1])
        db_type = db_cnx["main"]["type"]
        self.config["SQLALCHEMY_DATABASE_URI"] = uri

        for key, cf_db in db_cnx.items():
            self.config["SQLALCHEMY_BINDS"] = {x: y["cnx"] for x, y in db_cnx.items()}

        # self.api.config["MYSQL_DATABASE_CHARSET"]           = "utf8mb4"
        # self.api.config["QLALCHEMY_TRACK_MODIFICATIONS"]    = True
        # self.api.config["EXPLAIN_TEMPLATE_LOADING"]         = True
        self.config["UPLOAD_FOLDER"] = self.root_path

    def init(self, encode_rules={}):
        routes = self.conf.get("routes")
        if routes is not None:
            for route in routes:
                module = importlib.import_module(route)
        self.cache_dir = self.conf.get("directories/cache")

        # check request
        # ! freeze - dont know why
        """db              = core.get_database("main")
        request_model    = database_lib.get_table("main", "request")
        try:
            self.log.debug("Check <request> table")
            obj = db.exist(request_model)
        except:
            self.log.info("Creating <request> table")
            request_model.__table__.create(db.engine)"""

        # Flask configuration
        # todo: check JWT_SECRET_KEY: mandatory
        confs = self.conf.get("config")
        if confs is not None:
            for key, value in confs.items():
                self.config[key] = value

        self.json_encoder = AlphaJSONEncoder
        for key_rule, fct in encode_rules.items():
            AlphaJSONEncoder.rules[key_rule] = fct

        self.config["SECRET_KEY"] = b'_5#y2L"F4Q8z\n\xec]/'

        # MAILS
        mail_config = self.get_config("mails/mail_server")

        if mail_config is not None:
            self.config.update(
                MAIL_USE_TLS=mail_config["tls"],
                MAIL_USE_SSL=mail_config["ssl"],
                MAIL_SERVER=mail_config["server"],
                MAIL_PORT=mail_config["port"],
                MAIL_USERNAME=mail_config["mail"],
                MAIL_PASSWORD=mail_config["password"],
            )
            self.mail = Mail(self)
        else:
            self.log.error(
                'Mail configuration is not defined ("mails/mail_server" parameter)'
            )

        if self.conf.get("toolbar"):
            self.log("Loading debug toolbar")
            toolbar = DebugToolbarExtension(self)

        if self.conf.get("dashboard/dashboard/active"):
            self.log("Loading dashboard")
            filepath = config_lib.write_flask_dashboard_configuration(core)
            if filepath is not None:
                self.log.info("Dashboard configured from %s" % filepath)
                flask_monitoringdashboard.config.init_from(file=filepath)
                flask_monitoringdashboard.bind(self)

        if self.conf.get("admin_databases"):
            self.log.info("Loading admin databases interface")
            self.init_admin_view()

        # Base.prepare(self.db.engine, reflect=True)

    def set_config(self, name, configuration=None, root=None):
        self.log.debug(
            "Set <%s> configuration for API from %s in %s" % (configuration, name, root)
        )
        self.config_path = root + os.sep + name + ".json"
        self.configuration = configuration

        self.conf = AlphaConfig(
            name=name, configuration=configuration, root=root, log=self.log
        )  # root=os.path.dirname(os.path.realpath(__file__))

        if self.conf.get("routes_no_log"):
            _colorations.WerkzeugColorFilter.routes_exceptions = self.conf.get(
                "routes_no_log"
            )

    def init_admin_view(self):
        views = flask_lib.load_views(self.log)
        endpoints = [x.endpoint for x in views]

        from ..database.views import views as alpha_views

        for view in alpha_views:
            if view.endpoint not in endpoints:
                views.append(view)

        self.admin_db = Admin(
            self, name=self.get_config("name"), template_mode="bootstrap3"
        )
        self.admin_db.add_views(*views)

    def start(self):
        if self.pid is not None:
            return

        ssl_context = None
        if self.conf.get("ssl"):
            ssl_context = (self.conf.get("ssl_cert"), self.conf.get("ssl_key"))

        host = self.conf.get("host")
        port = self.conf.get("port")
        threaded = self.conf.get("threaded")
        
        self.debug = self.conf.get("debug") if not "ALPHA_DEBUG" in os.environ else ("y" in os.environ["ALPHA_DEBUG"].lower() or "t" in os.environ["ALPHA_DEBUG"].lower())
        if self.debug:
            sys.dont_write_bytecode = True

        self.log.info(
            "Run api on host %s port %s %s"
            % (host, port, "DEBUG MODE" if self.debug else "")
        )

        mode = self.conf.get("mode")
        if 'ALPHA_API' in os.environ:
            mode = os.environ['ALPHA_API']

        # try:
        if mode == "wsgi":
            application = DebuggedApplication(self, True) if self.debug else self

            if host == "0.0.0.0" or host == "localhost" and os_lib.is_linux():
                host = ""
            self.log.info(
                "Running %sWSGI mode on host <%s> and port %s"
                % ("debug " if self.debug else "", host, port)
            )

            server = WSGIServer((host, port), application, log=self.log_requests.logger)
            server.serve_forever()
        else:
            # Get werkzueg logger
            log = logging.getLogger("werkzeug")
            log.addFilter(
                _colorations.WerkzeugColorFilter()
            )  # TODO: set in configuration
            log.disabled = self.conf.get("log") is None

            self.run(
                host=host,
                port=port,
                debug=self.debug,
                threaded=threaded,
                ssl_context=ssl_context,
            )

        # except SystemExit:
        #    self.info("API stopped")

    def stop(self, config_path=None):
        if config_path is None:
            config_path = self.config_path
        if self.config_path is None:
            return

        #self.set_config(config_path=config_path, configuration=self.configuration)

        pid = self.get_config(["tmp", "process"])

        os.kill(pid, 9)

        self.log.info("Process n°%s killed" % pid)

    def get_config(self, name=""):
        if "/" in name:
            name = name.split("/")
        conf = self.conf.get(name)
        return conf

    def get_url(self):
        ssl = self.get_config("ssl")
        pref = "https://" if ssl else "http://"
        return pref + self.get_config("host_public")

    def access_denied(self):
        self.get_current_route().access_denied()
   
    def get(self, name):
        route = self.get_current_route()
        if route is None:
            return None
        value       = route.get(name)
        if (value is not None) and (value.startswith('*') or value.endswith('*')):
            value   = value.replace('*','%')
        return value

    def __getitem__(self, key):
        return self.get(key)

    def error(self, message):
        if self.log is not None:
            self.log.error(message, level=4)

    def info(self, message):
        if self.log is not None:
            self.log.info(message, level=4)

    def warning(self,message): 
        if self.log is not None:
            self.log.warning(message,level=4)

    def send_mail(self, mail_config, parameters_list, db, sender=None):
        # Configuration
        main_mail_config = self.get_config(["mails"])
        config = self.get_config(["mails", "configurations", mail_config])
        if config is None or type(config) != dict:
            self.log.error(
                'Missing "%s" mail configuration in "%s"' % (config, self.config_path)
            )
            return False

        # Parameters
        root_config = copy.copy(main_mail_config["parameters"])
        for key, parameter in main_mail_config["parameters"].items():
            root_config[key] = parameter

        # Sender
        if sender is None:
            if "sender" in config:
                sender = config["sender"]
            elif "sender" in main_mail_config:
                sender = main_mail_config["sender"]
            elif "sender" in main_mail_config["parameters"]:
                sender = main_mail_config["parameters"]["sender"]
            else:
                self.set_error("sender_error")
                return False

        full_parameters_list = []
        for parameters in parameters_list:
            # root_configuration          = copy.deepcopy(self.get_config())

            parameters_config = {}
            if "parameters" in config:
                parameters_config = copy.deepcopy(config["parameters"])

            full_parameters = {"title": config["title"]}

            _utils.fill_config(parameters_config, source_configuration=parameters)
            _utils.fill_config(root_config, source_configuration=parameters)
            _utils.fill_config(root_config, source_configuration=parameters_config)
            _utils.fill_config(parameters_config, source_configuration=root_config)
            _utils.fill_config(parameters, source_configuration=parameters_config)
            _utils.fill_config(parameters, source_configuration=root_config)

            _utils.merge_configuration(
                full_parameters, source_configuration=root_config, replace=True
            )
            _utils.merge_configuration(
                full_parameters, source_configuration=parameters_config, replace=True
            )
            _utils.merge_configuration(
                full_parameters, source_configuration=parameters, replace=True
            )

            full_parameters_list.append(full_parameters)

        mail_lib.KEY_SIGNATURE = (self.get_config("mails/key_signature"),)
        valid = mail_lib.send_mail(
            mail_path=self.get_config("mails/path"),
            mail_type=config["mail_type"],
            parameters_list=full_parameters_list,
            sender=sender,
            db=db,
            log=self.log,
        )
        if not valid:
            self.set_error("mail_error")
        return valid

    def get_current_route(self) -> Route:
        """Return the current route.

        Returns:
            Route: [description]
        """
        request_uuid = self.get_uuid()

        if request_uuid in self.routes_objects:
            return self.routes_objects[request_uuid]

        default_route = Route(request_uuid, request.full_path, [])
        if request_uuid not in self.routes_objects:
            self.log.critical("Cannot get route for %s" % request_uuid, monitor="DB")
            return default_route
        
        self.log.critical("Issue with route %s" % request_uuid, monitor="DB")
        return default_route

    def check_is_admin(self) -> bool:
        """Check if user is an admin or not.

        Args:
            log ([type], optional): [description]. Defaults to None.

        Returns:
            bool: [description]
        """
        route = self.get_current_route()

        user_data = _utils.get_logged_user()
        if user_data is not None:
            if user_data["role"] >= 9:
                return True
            else:
                self.warning("Wrong permission: %s is not an admin"%user_data)

        admin_password = self.conf.get("admin_password")
        if route["admin"] and admin_password is not None:
            if secure_lib.check_magic_code(self["admin"], admin_password):
                return True

        ip = request.remote_addr
        admins_ips = self.conf.get("admins")
        if admins_ips and (ip in admins_ips or "::ffff:%s" % ip in admins_ips):
            return True
        else:
            self.warning("Wrong permission: %s is not an admin"%ip)
        return False

    def get_logged_user(self):
        return _utils.get_logged_user()