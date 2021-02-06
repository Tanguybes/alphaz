import re

from typing import Dict

EXCEPTIONS = {}


def get_message_from_name(name):
    if type(name) != str:
        name = str(name)
    return name.replace("_", " ").capitalize()


class AlphaException(Exception):
    def __init__(self, name, description=None, parameters: Dict[str, object] = {}):
        self.name = name

        if name in EXCEPTIONS:
            if not "text" in EXCEPTIONS[name]:
                raise AlphaException(
                    "wrong_exception_definition",
                    "Wrong exception definition for %s" % name,
                )
            self.description = EXCEPTIONS[name]["text"]
        else:
            self.description = description or get_message_from_name(name)

        if len(parameters) != 0 and type(parameters) == dict:
            # parameters = re.findall(r'{[a-zA-Z_-]+',self.description)
            parameters_values = []
            for key, value in parameters.items():
                if "{%s" % key in self.description:
                    self.description = self.description.replace("{%s" % key, "{")
                    parameters_values.append(value)
            try:
                self.description = self.description.format(*parameters_values)
            except Exception as ex:
                raise AlphaException(
                    "wrong_exception_parameter",
                    "Wrong parameters for exception %s" % name,
                )

        super().__init__(self.description)
