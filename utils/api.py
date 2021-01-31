import traceback
from flask import (
    request,
    send_file,
    send_from_directory,
    safe_join,
    abort,
    url_for,
    render_template,
)

from ..models.main import AlphaException
from ..models.api import Parameter
from ..models.api._route import Route

from core import core

api = core.api
db = core.db
log = core.get_logger("api")

ROUTES = {}

# Specify the debug panels you want
# api.config['DEBUG_TB_PANELS'] = [ 'flask_debugtoolbar.panels.versions.VersionDebugPanel', 'flask_debugtoolbar.panels.timer.TimerDebugPanel', 'flask_debugtoolbar.panels.headers.HeaderDebugPanel', 'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel', 'flask_debugtoolbar.panels.template.TemplateDebugPanel', 'flask_debugtoolbar.panels.sqlalchemy.SQLAlchemyDebugPanel', 'flask_debugtoolbar.panels.logger.LoggingPanel', 'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel', 'flask_debugtoolbar_lineprofilerpanel.panels.LineProfilerPanel' ]
# toolbar = flask_debugtoolbar.DebugToolbarExtension(api)

def route(
    path,
    parameters=None,
    methods=["GET"],
    cache=False,
    logged=False,
    admin=False,
    timeout=None,
    cat=None,
    description=None
):
    if path[0] != "/":
        path = "/" + path

    parameters_error = None
    if parameters is None:
        parameters = []
    for i, parameter in enumerate(parameters):
        if type(parameter) == str:
            parameters[i] = Parameter(parameter)

    parameters.append(Parameter("reset_cache", ptype=bool, default=False, private=True))
    parameters.append(Parameter("requester", ptype=str, private=True))
    parameters.append(Parameter("format", ptype=str, default="json", private=True))

    def api_in(func):
        @api.route(path, methods=methods, endpoint=func.__name__)
        def api_wrapper(*args, **kwargs):
            if path not in ["/", "/status"]:
                log.debug(
                    "get api route {:10} with method <{}>".format(path, func.__name__)
                )

            #uuid_request = path + "&".join("%s=%s"%(x.name,x.value) for x in parameters if not x.private)
            uuid_request = api.get_uuid()
            # ROUTES
            __route = Route(
                uuid_request, path, parameters, cache=cache, timeout=timeout,
                cache_dir = api.cache_dir,
                log=api.log,
                jwt_secret_key="" if not "JWT_SECRET_KEY" in api.config else api.config["JWT_SECRET_KEY"]
            )
            api.routes_objects[uuid_request] = __route
            api.routes_objects = {x:y for x,y in api.routes_objects.items() if not y.is_outdated()}

            for parameter in parameters:
                try:
                    parameter.set_value()
                except Exception as ex:
                    __route.set_error(ex)
                    return __route.get_return()

            # check permissions
            if logged:
                user = api.get_logged_user()
                token = __route.get_token()
                if logged and token is None:
                    log.warning("Wrong permission: empty token")
                    __route.access_denied()
                    return __route.get_return()
                elif logged and (user is None or len(user) == 0):
                    log.warning("Wrong permission: wrong user", user)
                    __route.access_denied()
                    return __route.get_return()

            if admin and not api.check_is_admin():
                __route.access_denied()
                return __route.get_return()

            """data = api.get_current_route().get_return()
            api.delete_current_route()
            return  __route.get_return()"""

            cached = __route.keep()
            if cached:
                cached = __route.get_cached()

            if not cached:
                try:
                    output = func(*args, **kwargs)
                    if output == "timeout":
                        __route.timeout()
                    elif output is not None:
                        __route.set_data(output)
                except Exception as ex:
                    if (
                        api.get("error_format")
                        and api.get("error_format").lower() == "exception"
                    ):
                        raise ex
                    if not "alpha" in str(type(ex)).lower():
                        raise AlphaException(ex)
                    else:
                        __route.set_error(ex)
                if __route.cache:
                    __route.set_cache()

            data = __route.get_return()
            #api.delete_current_route()
            return data

        api_wrapper.__name__ = func.__name__

        if cache:
            parameters.append(Parameter("reset_cache", ptype=bool, cacheable=False))

        if not "cat" in locals() or cat is None:
            category = func.__module__.split(".")[-1]
        else:
            category = cat.lower()

        kwargs_ = {
            "path": path,
            "parameters": parameters,
            "parameters_names": [x.name for x in parameters],
            "methods": methods,
            "cache": cache,
            "logged": logged,
            "admin": admin,
            "timeout": timeout,
            "category": category,
            "description": description
        }
        api_wrapper._kwargs = kwargs_

        paths = [x for x in path.split("/") if x.strip() != ""]
        if len(paths) == 1:
            paths = ["root", paths[0]]

        arguments = {
            x: y if x != "parameters" else [j.__dict__ for j in y]
            for x, y in kwargs_.items()
        }

        trace = traceback.format_stack()

        ROUTES[path] = {
            "category": category,
            "name": func.__name__,
            "module": "",
            "paths": paths,
            "arguments": arguments,
        }

        return api_wrapper

    return api_in


##################################################################################################################
# BASE API FUNCTIONS
##################################################################################################################


@api.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add(
        "Access-Control-Allow-Headers",
        "Origin,Accept,X-Requested-With,Content-Type,Authorization",
    )
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    # response.headers.set('Allow', 'GET, PUT, POST, DELETE, OPTIONS')
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response

