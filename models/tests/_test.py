
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
        self.output = None
        status = False
        fct = getattr(self,name)
        if fct is None:
            LOG.info('Failed to get testing function <%s> in category <%s>'%(name,category))
            return False
        try:
            status = fct()
            if self.output is not None:
                status = self.output
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

    def _set_output(self,status):
        if self.output is not None:
            self.output = status and self.output
        else:
            self.output = status

    def array_equal(self,a,b):
        equal = len(a) == len(b)
        if equal:
            for i in range(len(a)):
                if a[i] != b[i]: 
                    equal = False

        if not equal:
            LOG.debug("Arrays size are not equal: <%s> and <%s>"%(len(a),len(b)))
        self._set_output(equal)

    def assert_is_not_empty(self, a, conditions = [], attribute=None):
        if attribute is not None:
            if not hasattr(a,attribute):
                LOG.error('Object of type <%s> does not have an attribute named <%s>'%(type(a),attribute))
            status = a is not None and not len(getattr(a,attribute)) == 0
        elif isinstance(a,pd.DataFrame):
            status = a is not None and not a.empty
        else:
            status = a is not None and len(a) != 0

        if len(conditions) != 0 and type(conditions) == list:
            status = status and all(conditions)
        self._set_output(status)
        
    def assert_length(self, a, length):
        status = a is not None and len(a) != 0 and len(a) == length
        self._set_output(status)
