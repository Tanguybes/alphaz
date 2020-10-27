import datetime, re

from core import core
from ..database.main_definitions import Tests

log = core.get_logger('tests')

class AlphaTable():
    def update_from(self,source):
        for key in self.__dict__.keys():
            if hasattr(source,key):
                source_element = getattr(source,key)
                self.__dict__[key] = source_element

class TestMethod(AlphaTable):
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
        
    def test(self,verbose=False):
        classObject             = self.classObject()
        classObject.verbose     = verbose

        self.start_time         = datetime.datetime.now()
        
        log.info('Testing function <%s> of <%s> in category <%s>'%(self.name,type(self).__name__,self.category))

        self.status             = classObject.test(self.name)

        log.info('Function <%s> of <%s> in category <%s>: %s'%(
            self.name,type(self).__name__,self.category,'X' if not self.status else 'O'))

        self.end_time           = datetime.datetime.now()
        self.elapsed            = (self.end_time - self.start_time).total_seconds()

        self.update_database()

        return self.status

    def update_database(self):
        test = Tests(
            category=self.category, 
            group=self.group,
            name=self.name,
            status=self.status,
            start_time=self.start_time,
            end_time=self.end_time,
            elapsed=self.elapsed
        )
        core.db.add(test)

    def get_from_database(self):
        test = core.db.select(Tests,filters=[Tests.category==self.category,Tests.group==self.group,Tests.name==self.name],
            order_by=Tests.start_time.desc(),first=True)
        self.update_from(test)

    def save(self,verbose=False):
        classObject         = self.classObject()
        classObject.verbose = verbose
        classObject.save(self.name)

    def is_valid(self):
        return self.status != None and self.status

    def print(self):
        return 'OK' if self.status else 'X'

    def to_json(self):
        return {
            'status': self.status,
            'elapsed': self.elapsed,
            'end_time': self.start_time
        }