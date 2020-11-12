
import traceback
from core import core

import pandas as pd

from ._save import AlphaSave

LOG = core.get_logger('tests')

class AlphaTest():
    _test = True
    category = ''

    def __init__(self):
        self.output: bool = None

    def test(self,name):
        status = False
        fct = getattr(self,name)
        if fct is None:
            LOG.info('Failed to get testing function <%s> in category <%s>'%(name,category))
            return False
        try:
            status = fct()
        except Exception as ex:
            text    = traceback.format_exc()
            LOG.error(text)
        return status

    def save(self,name):
        fct = getattr(self,name)
        if fct is None:
            return False
            
        if inspect.unwrap(fct).__name__ == save_method_name:
            object_to_save      = fct(get_return=True)
            object_name_to_save = fct(get_name=True)
            AlphaSave.save(object_to_save,object_name_to_save)

    def array_equal(self,a,b):
        equal = len(a) == len(b)
        if equal:
            for i in range(len(a)):
                if a[i] != b[i]: 
                    equal = False

        LOG.debug("Arrays size are not equal: <%s> and <%s>"%(len(a),len(b)))
        self.output = equal

    def assert_is_not_empty(self, a, conditions = []):
        if isinstance(a,pd.DataFrame):
            self.output = a is not None and not a.empty
        else:
            self.output = a is not None and len(a) != 0

        if len(conditions) != 0 and type(conditions) == list:
            self.output = self.output and all(conditions)

    def assert_length(self, a, length):
        self.output = a is not None and len(a) != 0 and len(a) == length
