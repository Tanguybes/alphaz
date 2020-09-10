from flask import url_for

from ...utils.api import route, Parameter

from ..main import get_routes_infos

from core import core

api         = core.api
db          = core.db
log         = core.get_logger('api')

category    = 'api'

@route("/map",category=category)
def api_map():
    api.set_data(get_routes_infos(log=log))


def has_no_empty_params(rule):
    defaults    = rule.defaults if rule.defaults is not None else ()
    arguments   = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)

@route("/routes",category=category,parameters=[
    Parameter('admin',default=False,ptype=bool)
])
def site_map():
    links = []
    for rule in api.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))

            if not api.get('admin') and '/admin' in url:
                continue

            links.append((url, rule.endpoint))
    api.set_data(links)