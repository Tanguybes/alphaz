import datetime, os
from typing import List, Dict

from flask import (
    Flask,
    jsonify,
    request,
    Response,
    make_response,
    render_template,
    send_from_directory,
)

from ...libs import json_lib, converter_lib, io_lib

from ._parameter import Parameter

SEPARATOR = "::"


def check_format(data, depth=3):
    if depth == 0:
        return True

    accepted = [int, str, float]
    if type(data) in accepted:
        return True

    if type(data) == list and len(data) != 0:
        return check_format(data[0], depth - 1)
    if type(data) == dict and len(data) != 0:
        return check_format(list(data.keys())[0], depth - 1) & check_format(
            list(data.values())[0], depth - 1
        )
    return False


class Route:
    def __init__(
        self,
        api,
        uuid: str,
        route: str,
        parameters: List[Parameter],
        cache: bool = False,
        timeout=None,
    ):
        self.api = api
        self.__timeout = timeout
        self.uuid: str = uuid
        self.route: str = route
        self.cache: bool = cache

        self.parameters: Dict[Parameter] = {y.name: y for y in parameters}

        self.lasttime = datetime.datetime.now()

        self.mode = "data"

        self.data = {}
        self.returned = {}

        self.html = {"page": None, "parameters": None}
        self.message = "No message"

        self.file_to_get = (None, None)
        self.file_to_set = (None, None)

    def get(self, name):
        if not name in self.parameters:
            return None

        parameter = self.parameters[name]
        value = None if parameter is None else parameter.value
        if str(value) == "false":
            return False
        if str(value) == "true":
            return True
        return value

    def __getitem__(self, key):
        return self.get(key)

    def is_time(self, timeout):
        is_time = False
        if timeout is not None:
            now = datetime.datetime.now()
            lastrun = self.lasttime
            nextrun = lastrun + datetime.timedelta(minutes=timeout)
            is_time = now > nextrun
        return is_time

    def keep(self):
        reset_cache = self.get("reset_cache") or self.is_time(self.__timeout)
        if not self.cache:
            return False and not reset_cache
        key = self.get_key()
        # return_cache    = key in self.routes_values.keys()
        # return return_cache and not reset_cache
        return not reset_cache

    def get_key(self):
        key = "%s%s" % (self.route, SEPARATOR)
        for name, parameter in self.parameters.items():
            if parameter.cacheable and not parameter.private:
                key += "%s=%s;" % (parameter.name, parameter.value)
        return key

    def get_cache_path(self):
        cache_dir = self.api.conf.get("directories/cache")
        if cache_dir is None:
            return None
        key = self.get_key()
        cache_path = cache_dir + os.sep + key + ".cache"
        return cache_path

    def set_cache(self):
        self.lasttime = datetime.datetime.now()
        cache_path = self.get_cache_path()
        if cache_path is None:
            self.api.log.error("cache path does not exist")
            return
        returned = io_lib.archive_object(self.data, cache_path)

    def get_cached(self):
        if self.api.log:
            self.api.log.info("   GET cache for %s" % self.route)

        cache_path = self.get_cache_path()
        if cache_path is None:
            self.api.log.error("cache path does not exist")
            return False
        if os.path.exists(cache_path):
            data = io_lib.unarchive_object(cache_path)
            if data:
                self.init_return()
                self.set_data(data)
                return True

        self.set_error("No cache")
        return False

    def set_status(self, status):
        self.returned["status"] = status

    def timeout(self):
        self.returned["status"] = "timeout"
        self.returned["error"] = 1

    def access_denied(self):
        self.returned["token_status"] = "denied"
        self.returned["error"] = 1
        self.returned["status"] = 401

    def set_error(self, message: str, description: str = None):
        self.mode == "data"
        self.returned["status"] = message
        self.returned["status_description"] = description if description else message
        self.returned["error"] = 1

    def print(self, message):
        self.mode == "print"
        self.message = message

    def init_return(self):
        returned = {"token_status": "success", "status": "success", "error": 0}
        self.file_to_get = (None, None)
        self.file_to_set = (None, None)
        self.returned, self.data = returned, {}

    def set_data(self, data):
        self.mode == "data"
        self.data = data

    def set_file(self, directory, filename):
        self.mode = "set_file"
        self.file_to_set = (directory, filename)

    def get_file(self, directory, filename, attached=False):
        self.mode = "get_file" if not attached else "get_file_attached"
        self.file_to_get = (directory, filename)

    def set_html(self, page, parameters={}):
        self.mode = "html"
        self.html = {"page": page, "parameters": parameters}

    def get_return(self, forceData=False, return_status=None):
        if self.mode == "html":
            return render_template(self.html["page"], **self.html["parameters"])
        if self.mode == "print":
            return self.message

        if "get_file" in self.route:
            file_path, filename = self.file_to_get
            if file_path is not None and filename is not None:
                self.api.info("Sending file %s from %s" % (filename, file_path))
                try:
                    return send_from_directory(
                        file_path,
                        filename=filename,
                        as_attachment="attached" in self.mode,
                    )
                except FileNotFoundError:
                    self.api.set_error("missing_file")
            else:
                self.api.set_error("missing_file")

        if isinstance(self.data, Exception):
            if hasattr(self.data, "msg"):
                self.set_error(self.data.msg, self.data.msg)
            elif hasattr(self.data, "args"):
                self.set_error(self.data.args[0], self.data.args[0])
            self.data = {}

        self.returned["data"] = {}

        data = {} if self.data is None else self.data

        # Convert
        self.returned["data"] = data
        if not check_format(data):
            self.returned["data"] = json_lib.jsonify_data(data)

        format_ = self.get("format")
        if format_ and "xml" in format_.lower():
            xml_output = converter_lib.dict_to_xml(
                self.returned, attr_type=not "no_type" in format_
            )
            response = make_response(xml_output)
            response.headers["Content-Type"] = "text/xml; charset=utf-8"
            return response
        else:
            returned = jsonify(self.returned)
            if "status" in self.returned and type(self.returned["status"]) == int:
                returned.status_code = self.returned["status"]

        return returned

    def log_user(self, user_data):
        self.returned["role"] = "user"
        if user_data["role"] >= 9:
            self.returned["role"] = "admin"
        self.returned["token"] = jwt.encode(
            {
                "username": user_data["username"],
                "id": user_data["id"],
                "time": str(datetime.datetime.now()),
            },
            api.config["JWT_SECRET_KEY"],
            algorithm="HS256",
        ).decode("utf-8")
        self.returned["valid_until"] = datetime.datetime.now() + datetime.timedelta(
            days=7
        )

