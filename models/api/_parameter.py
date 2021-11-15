import json, datetime
from flask import request
from sqlalchemy.orm.base import object_mapper
from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.ext.declarative import DeclarativeMeta

from collections.abc import Callable

from ..main import AlphaException

from ...libs import date_lib, json_lib

from enum import Enum


class ParameterMode(Enum):
    NONE = 0
    LIKE = 1
    IN_LIKE = 2
    START_LIKE = 3
    END_LIKE = 4


class Parameter:
    def __init__(
        self,
        name: str,
        default=None,
        options=None,
        cacheable: bool = True,
        required: bool = False,
        ptype: type = str,
        private: bool = False,
        mode: ParameterMode = ParameterMode.NONE,
        override: bool = False,
        function: Callable = None,
    ):
        """[summary]

        Args:
            name (str): [description]
            default ([type], optional): [description]. Defaults to None.
            options ([type], optional): [description]. Defaults to None.
            cacheable (bool, optional): [description]. Defaults to True.
            required (bool, optional): [description]. Defaults to False.
            ptype (type, optional): [description]. Defaults to str.
            private (bool, optional): [description]. Defaults to False.
            mode (str, optional): [description]. Defaults to "none".
        """
        self.name = name
        self.default = default
        self.cacheable = cacheable
        self.options = options
        self.required = required
        self.ptype: type = ptype
        self.function: Callable = function
        self.type = str(ptype).replace("<class '", "").replace("'>", "")
        self.value = None
        self.private = private
        self.mode = mode
        self.override = override

    def __check_options(self, value):
        if (
            self.options is not None
            and value not in self.options
            and not (not self.required and value is None)
        ):
            raise AlphaException(
                "api_wrong_parameter_option",
                parameters={
                    "parameter": self.name,
                    "options": str(self.options),
                    "value": value,
                },
            )

    def set_value(self):
        """Set parameter value

        Raises:
            AlphaException: [description]
            AlphaException: [description]
            AlphaException: [description]
            AlphaException: [description]
            AlphaException: [description]
            AlphaException: [description]
        """

        dataPost = request.get_json()

        self.value = request.args.get(self.name, self.default)

        if self.value is None and dataPost is not None and self.name in dataPost:
            self.value = dataPost[self.name]
        if (
            self.value is None
            and request.form is not None
            and self.name in request.form
        ):
            self.value = request.form[self.name]

        if isinstance(self.ptype, DeclarativeMeta):
            if self.value is None:
                parameters = {
                    x: y for x, y in dataPost.items() if hasattr(self.ptype, x)
                }
            else:
                parameters = json_lib.load_json(self.value)
            self.value = self.ptype(**parameters)

        if self.required and self.value is None:
            missing = True
            raise AlphaException(
                "api_missing_parameter", parameters={"parameter": self.name}
            )

        if self.value is None:
            self.__check_options(self.value)
            return

        if str(self.value).lower() in ["null", "none", "undefined"]:
            self.value = None

        if self.ptype == str and (
            self.mode
            in [
                ParameterMode.LIKE,
                ParameterMode.IN_LIKE,
                ParameterMode.START_LIKE,
                ParameterMode.END_LIKE,
            ]
        ):
            self.value = str(self.value).replace("*", "%")

            if not "%" in self.value:
                if (
                    self.mode
                    in [
                        ParameterMode.IN_LIKE,
                        ParameterMode.START_LIKE,
                    ]
                    and not self.value.startswith("%")
                ):
                    self.value = f"%{self.value}"
                if (
                    self.mode
                    in [
                        ParameterMode.IN_LIKE,
                        ParameterMode.END_LIKE,
                    ]
                    and not self.value.endswith("%")
                ):
                    self.value = f"{self.value}%"

        if self.ptype == bool:
            str_value = str(self.value).lower()
            self.__check_options(str(self.value))

            if str_value in ["y", "true", "t", "1"]:
                value = True
            elif str_value in ["n", "false", "f", "0"]:
                value = False
            else:
                raise AlphaException(
                    "api_wrong_parameter_value",
                    parameters={
                        "parameter": self.name,
                        "type": "bool",
                        "value": self.value,
                    },
                )
            self.value = value

        if self.ptype == list:
            if type(self.value) == str and self.value.strip() == "":
                self.value = []
            elif type(self.value) == str:
                try:
                    if ";" in str(self.value) or "," in str(self.value):
                        self.value = (
                            str(self.value).split(";")
                            if ";" in str(self.value)
                            else str(self.value).split(",")
                        )
                    else:
                        self.value = [self.value]
                except:
                    raise AlphaException(
                        "api_wrong_parameter_value",
                        parameters={
                            "parameter": self.name,
                            "type": "list",
                            "value": self.value,
                        },
                    )
            for val in self.value:
                self.__check_options(val)

        if self.ptype == int:
            try:
                self.value = int(self.value)
            except:
                raise AlphaException(
                    "api_wrong_parameter_value",
                    parameters={
                        "parameter": self.name,
                        "type": "int",
                        "value": self.value,
                    },
                )
            self.__check_options(self.value)

        if self.ptype == float:
            try:
                self.value = float(self.value)
            except:
                raise AlphaException(
                    "api_wrong_parameter_value",
                    parameters={
                        "parameter": self.name,
                        "type": "float",
                        "value": self.value,
                    },
                )
            self.__check_options(self.value)

        if self.ptype == datetime.datetime:
            self.__check_options(self.value)
            self.value = date_lib.str_to_datetime(self.value)

        if hasattr(self.ptype, "metadata") and not hasattr(self.value, "metadata"):
            r = json.loads(self.value)
            self.value = self.ptype(**r)

        if self.function is not None:
            self.value = self.function(self.value)
