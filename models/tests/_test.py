from core import core

from ._save import AlphaSave

log = core.get_logger('tests')

class AlphaTest():
    category = ''

    def __init__(self,verbose=False):
        self.verbose = verbose
        self.output = True

    def test(self,name):
        status = False
        fct = getattr(self,name)
        if fct is None:
            log.info('Failed to get testing function <%s> in category <%s>'%(name,category))
            return False
        try:
            status = fct()
        except Exception as ex:
            log.error(ex)
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
        elif self.verbose:
            log.warning("Arrays size are not equal: <%s> and <%s>"%(len(a),len(b)))
        return equal
