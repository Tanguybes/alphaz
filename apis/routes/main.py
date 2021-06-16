import datetime

from alphaz.libs import dict_lib

from flask import request, send_from_directory

from ...libs import test_lib, database_lib, api_lib, transactions_lib
from ...utils.api import route, Parameter
from ...utils.time import tic, tac
from ...models.main import AlphaException

from core import core

api = core.api
db = core.db
LOG = core.get_logger("api")


@api.route("/assets/<path:path>")
def send_js(path):
    return send_from_directory("assets", filename=path)


@api.route("/images/<path:path>")
def send_images(path):
    return send_from_directory("images", filename=path)


@route("/page", parameters=[Parameter("page", required=True, ptype=str)])
def index():
    api.set_html(api.get("page"))


@route("/profil/pic", logged=True)
def get_profil_pic():
    file_path = core.config.get("directories/images")
    api.get_file(file_path, api.get_logged_user()["id"])


@route("/files/upload", logged=True, methods=["POST"])
def upload_file():
    uploaded_file = request.files["file"]
    ext = uploaded_file.filename.split(".")[1]
    filename = str(api.get_logged_user()["id"]) + "." + ext

    file_path = core.config.get("directories/images")
    api.set_file(file_path, filename)


@route("status")
def status():
    return True


@route("/")
def home():
    config = api.conf

    tests = None
    try:
        tests = test_lib.get_tests_auto(core.config.get("directories/tests"))
    except Exception as ex:
        LOG.error(ex)

    parameters = {
        "mode": core.config.configuration,
        "mode_color": "#e74c3c"
        if core.config.configuration == "prod"
        else ("#0270D7" if core.config.configuration == "dev" else "#2ecc71"),
        "title": config.get("templates/home/title"),
        "description": config.get("templates/home/description"),
        "year": datetime.datetime.now().year,
        "users": 0,
        "ip": request.environ["REMOTE_ADDR"],
        "admin": config.get("admin_databases"),
        "routes": api_lib.get_routes_infos(log=LOG),
        "compagny": config.get("parameters/compagny"),
        "compagny_website": config.get("parameters/compagny_website"),
        "dashboard": config.get("dashboard/dashboard/active"),
        "tests": tests,
        "databases": database_lib.get_databases_tables_dict(core),
    }
    api.set_html("home.html", parameters=parameters)

@route("doc", mode="html")
def doc():
    try:
        import markdown2
    except:
        raise AlphaException("import_error", {"module":"markdown"})

    with open("alphaz/help.md","r") as f:
        content = f.read()
        html = markdown2.markdown(content)
        return html

@route("loggers")
def get_loggers():
    return core.config.loggers

@route("logger/level", parameters=[
    Parameter("name",required=True),
    Parameter("level", options=["info","warnings","error","debug"])
])
def set_logger_level():
    logger = core.config.get_logger(api["name"])
    if logger is None:
        raise AlphaException("no_logger")
    logger.set_level(api["level"])

@route("infos")
def get_infos():
    import getpass, platform
    return {
        "user":getpass.getuser(), 
        "system":platform.uname().system,
        "node":platform.uname().node,
        "release":platform.uname().release,
        "version":platform.uname().version,
        "machine":platform.uname().machine,
        "processor":platform.uname()[4]
    }

@route("modules", parameters=[Parameter("name")])
def get_modules():
    from importlib.metadata import version
    import pkgutil
    data = {}
    for item in pkgutil.iter_modules():
        if api["name"] is not None and api["name"].lower() != item.name.lower():
            continue
        try:
            data[item.name] = version(item.name)
        except:
            continue
    return data