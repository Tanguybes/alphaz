import re

from ...libs import io_lib

class ColorFilter:
    def __init__(self,configuration):
        self.configuration = configuration

    def filter(self, record):
        patterned = []

        msg = record.msg

        for pattern, pattern_config in self.configuration.items():
            #pattern = pattern.replace('\\\\','\\').replace(r"\\+",r"\+")
            results = re.findall(pattern, msg)
            for result in results:
                if not result in patterned:
                    msg = msg.replace(result,io_lib.colored_term(result,
                        front=pattern_config.get('color',None),
                        back=pattern_config.get('background',None),
                        bold=pattern_config.get('bold',None)
                    ))
                    patterned.append(result)

        record.msg = msg
        return record