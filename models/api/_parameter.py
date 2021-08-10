import json, datetime
from flask import request
from sqlalchemy.orm.base import object_mapper
from sqlalchemy.orm.exc import UnmappedInstanceError

from collections.abc import Callable

from ..main import AlphaException

from ...libs import date_lib

class Parameter:
    def __init__(
        self,
        name: str,
        default=None,
        options=None,
        cacheable: bool=True,
        required: bool=False,
        ptype: type=str,
        private: bool=False,
        mode: str="none",
        override: bool=False,
        function: Callable=None
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

    def set_value(self):
        """ Set parameter value

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
        if self.value is None and request.form is not None and self.name in request.form:
            self.value = request.form[self.name]

        if (
            self.options is not None
            and self.value not in self.options
            and not (not self.required and self.value is None)
        ):
            raise AlphaException(
                "api_wrong_parameter_option",
                parameters={
                    "parameter": self.name,
                    "options": str(self.options),
                    "value": self.value,
                },
            )

        if self.required and self.value is None:
            missing = True
            raise AlphaException(
                "api_missing_parameter", parameters={"parameter": self.name}
            )
        
        if self.value is None:
            return

        if self.ptype == str and self.mode == "like":
            self.value = str(self.value)
            if (self.value is not None) and (self.value.startswith('*') or self.value.endswith('*')):
                self.value = self.value.replace('*', '%')

        if self.ptype == bool:
            str_value = str(self.value).lower()
            if str_value in ["y", "true", "t", "1"]:
                value = True
            elif str_value in ["n", "false", "f", "0"]:
                value = False
            else:
                raise AlphaException(
                    "api_wrong_parameter_value",
                    parameters={"parameter": self.name, "type": "bool", "value":self.value},
                )
            self.value = value

        if self.ptype == list:
            if self.value.strip() == "":
                self.value = []
            else:
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
                        parameters={"parameter": self.name, "type": "list", "value":self.value},
                    )

        if self.ptype == int:
            try:
                self.value = int(self.value)
            except:
                raise AlphaException(
                    "api_wrong_parameter_value",
                    parameters={"parameter": self.name, "type": "int", "value":self.value},
                )

        if self.ptype == float:
            try:
                self.value = float(self.value)
            except:
                raise AlphaException(
                    "api_wrong_parameter_value",
                    parameters={"parameter": self.name, "type": "float", "value":self.value},
                )

        if self.ptype == datetime.datetime:
            self.value = date_lib.str_to_datetime(self.value)

        if hasattr(self.ptype, "metadata"):
            r = json.loads(self.value)
            self.value = self.ptype(**r)

        if self.function is not None:
            self.value = self.function(self.value)

