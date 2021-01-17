from flask import request

from ..main import AlphaException


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
    ):

        self.name = name
        self.default = default
        self.cacheable = cacheable
        self.options = options
        self.required = required
        self.ptype: type = ptype
        self.type = str(ptype).replace("<class '", "").replace("'>", "")
        self.value = None
        self.private = private

    def set_value(self):
        dataPost = request.get_json()

        self.value = request.args.get(self.name, self.default)

        if self.value is None and dataPost is not None and self.name in dataPost:
            self.value = dataPost[self.name]

        if (
            self.options is not None
            and self.value not in self.options
            and not (not self.required and self.value is None)
        ):
            raise AlphaException(
                "api_wrong_value_parameter",
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

        if self.ptype == bool and not self.value is None:
            str_value = str(self.value).lower()
            if str_value == "y":
                value = True
            elif str_value == "true":
                value = True
            elif str_value == "t":
                value = True
            elif str_value == "1":
                value = True
            elif str_value == "n":
                value = False
            elif str_value == "false":
                value = False
            elif str_value == "f":
                value = False
            elif str_value == "0":
                value = False
            else:
                raise AlphaException(
                    "api_wrong_parameter_value",
                    parameters={"parameter": self.name, "type": "bool"},
                )
            self.value = value

        if self.ptype == list and self.value is not None:
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
                    parameters={"parameter": self.name, "type": "list"},
                )

        if self.ptype == int and not self.value is None:
            try:
                self.value = int(self.value)
            except:
                raise AlphaException(
                    "api_wrong_parameter_value",
                    parameters={"parameter": self.name, "type": "int"},
                )

        if self.ptype == float and not self.value is None:
            try:
                self.value = float(self.value)
            except:
                raise AlphaException(
                    "api_wrong_parameter_value",
                    parameters={"parameter": self.name, "type": "float"},
                )

