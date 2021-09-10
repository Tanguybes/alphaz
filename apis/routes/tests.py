from ...utils.api import route, Parameter

from .. import tests

from ...libs import test_lib

from core import core

api = core.api
db = core.db
log = core.get_logger("api")


@route(
    "/tests",
    parameters=[
        Parameter("category", ptype=str),
        Parameter("categories", ptype=list),
        Parameter("group", ptype=str),
        Parameter("groups", ptype=list),
        Parameter("name", ptype=str),
        Parameter("names", ptype=list),
        Parameter("run", ptype=bool),
        Parameter("file_path", ptype=str),
    ],
)
def get_tests():
    return test_lib.get_tests_auto(
        core.config.get("directories/tests"), **api.get_parameters()
    )


@route("/tests/methods", methods=["GET"])
def get_method_1():
    return "GET"


@route("/tests/methods", methods=["POST"])
def get_method_2():
    return "POST"


@route("/tests/methods", methods=["PUT"])
def get_method_3():
    return "PUT"


@route("/tests/methods", methods=["PATCH"])
def get_method_4():
    return "PATCH"


@route("/tests/methods", methods=["DELETE"])
def get_method_5():
    return "DELETE"
