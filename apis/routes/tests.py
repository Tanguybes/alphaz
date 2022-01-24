from ...utils.api import route, Parameter

from .. import tests

from ...libs import test_lib, io_lib

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
        Parameter("coverage", ptype=str),
    ],
)
def get_tests():
    return test_lib.get_tests_auto(
        core.config.get("directories/tests"), **api.get_parameters()
    )


@route("/tests/coverage", parameters=[Parameter("file", required=True)])
def get_coverage_file():
    coverages = io_lib.unarchive_object(api["file"])
    return coverages

