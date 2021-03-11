import datetime, re

from core import core
from ..database.main_definitions import Tests

from ...libs import number_lib

log = core.get_logger('tests')

class TestMethod:
    def __init__(self,classObject,name:str,method,category:str,group:str):
        self.name:str           = name
        self.method             = method
        self.classObject        = classObject
        self.category:str       = category
        self.group:str          = group

        self.status:bool                     = None
        self.start_time:datetime.datetime   = None
        self.end_time:datetime.datetime     = None
        self.elapsed:int                    = None
        self.last_run_elapsed               = None
        
    def test(self,classObject=None):
        if classObject is None:
            classObject             = self.classObject()

        self.start_time         = datetime.datetime.now()
        
        log.info('Testing function <%s> of <%s> in category <%s>'%(self.name,type(self).__name__,self.category))

        result                  = classObject.test(self.name)
        classObject.end()
        self.status             = result if type(result) == bool else False

        log.info('Function <%s> of <%s> in category <%s>: %s'%(
            self.name,type(self).__name__,self.category,'X' if not self.status else 'O'))

        self.end_time           = datetime.datetime.now()
        self.elapsed            = (self.end_time - self.start_time).total_seconds()

        self.update_database()
        self._proceed()

        return self.status

    def update_database(self):
        test = Tests(
            category=self.category, 
            tests_group=self.group,
            name=self.name,
            status=self.status,
            start_time=self.start_time,
            end_time=self.end_time,
            elapsed=self.elapsed
        )
        core.db.add(test)

    def update_from(self,source):
        for key in self.__dict__.keys():
            if hasattr(source,key):
                source_element = getattr(source,key)
                if key == 'elapsed':
                    source_element = number_lib.myround(source_element,2)
                self.__dict__[key] = source_element

        self._proceed()

    def get_from_database(self):
        test = core.db.select(Tests,filters=[Tests.category==self.category,Tests.tests_group==self.group,Tests.name==self.name],
            order_by=Tests.start_time.desc(),first=True)
        self.update_from(test)

    def save(self):
        classObject         = self.classObject()
        classObject.save(self.name)

    def is_valid(self):
        return self.status != None and self.status

    def print(self):
        return 'OK' if self.status else 'X'

    def _proceed(self):
        self.last_run_elapsed = None if self.start_time is None else str(datetime.datetime.now() - self.start_time).split('.')[0]

    def to_json(self):
        return {
            "status": self.status,
            "elapsed": number_lib.myround(self.elapsed,2),
            "end_time": self.start_time,
            "last_run_elapsed": self.last_run_elapsed
        }