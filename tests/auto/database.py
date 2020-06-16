from alphaz.models.tests import AlphaTest, test
from core import core

from alphaz.libs import date_lib
import alphaz.models.database.definitions as defs
from alphaz.models.database.definitions import Test

class Dataframe(AlphaTest):
    connected      = False

    columns         = ['name','text','number','date','update']

    date_datetime   = date_lib.str_to_datetime('2020/01/07 10:02:03')
    parameters      = {'name': 'insert','text': "insert_text",'number': 12,
    'date':date_datetime}

    select_parameters      = {'name': 'select','text': "select",'number': 12}

    def __init__(self):
        super().__init__()

        self.db         = core.db
        self.connected  = self.db.test()

        if not self.connected:
            print('not connected')
            exit()
            return

        core.init_database(defs)

    @test(save=False)
    def connexion(self):
        return self.connected

    @test(save=False)
    def insert(self):
        return self.db.add(Test,self.parameters)

    @test(save=False)
    def insert2(self):
        return self.db.add(Test,{
            Test.name:      self.parameters['name'],
            Test.number:    self.parameters['number'],
            Test.text:      self.parameters['text'],
            Test.date:      self.parameters['date']
        })

    @test(save=False)
    def insert3(self):
        return self.db.add(Test(
            name=      self.parameters['name'],
            number=    self.parameters['number'],
            text=      self.parameters['text'],
            date=      self.parameters['date']
        ))

    @test(save=False)
    def select_dict(self):
        print('rrrr',Test.query.all())

        rows    = self.db.select(Test) # ,columns=self.columns
        valid   = len(rows) == 1
        if not valid:
            return False
        return rows[0] == self.select_parameters

    """@test(save=False)
    def delete(self):
        return self.db.delete(Test,parameters=self.parameters)
        
    @test(save=False)
    def select_unique(self):
        rows    = self.db.select(Test,columns=['name'],unique=True)
        valid   = len(rows) == 1
        if not valid:
            return False
        return rows[0] == 'select'

    @test(save=False)
    def select_dict_numbers(self):
        rows    = self.db.select(Test,columns=self.columns)
        valid   = len(rows) == 1
        if valid:
            parameters = rows[0]
            name    = parameters[0]
            text    = parameters[1]
            number  = parameters[2]
        return name == "select" and text == "select" and number == 12

    @test(save=False)
    def insert_or_update(self):
        return self.db.add(Test,parameters=self.parameters,update=True)"""
