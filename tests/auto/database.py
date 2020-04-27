from alphaz.models.tests import AlphaTest, test
from alphaz.core import core

class Dataframe(AlphaTest):
    connected      = False

    columns         = ['name','text','number']
    parameters      = {'name': 'insert','text': "insert",'number': 12}
    select_parameters      = {'name': 'select','text': "select",'number': 12}

    table           = 'test'

    def __init__(self):
        super().__init__()

        self.database = core.test_database

        self.connected = self.database.test()

        if not self.connected:
            return

        self.init()
    
    def init(self):
        self.database.execute('truncate table ' + self.table)
        self.database.execute("INSERT INTO `test` (`name`, `text`, `number`) VALUES ('select', 'select', 12);")

    @test(save=False)
    def connexion(self):
        return self.connected

    @test(save=False)
    def insert(self):
        return self.database.insert(self.table,parameters=self.parameters)

    @test(save=False)
    def select_dict(self):
        rows    = self.database.select(self.table,columns=self.columns)
        valid   = len(rows) == 1
        if not valid:
            return False
        return rows[0] == self.select_parameters

    @test(save=False)
    def delete(self):
        return self.database.delete(self.table,parameters=self.parameters)
        
    @test(save=False)
    def select_unique(self):
        rows    = self.database.select(self.table,columns=['name'],unique=True)
        valid   = len(rows) == 1
        if not valid:
            return False
        return rows[0] == 'select'

    @test(save=False)
    def select_dict_numbers(self):
        rows    = self.database.select(self.table,columns=self.columns)
        valid   = len(rows) == 1
        if valid:
            parameters = rows[0]
            name    = parameters[0]
            text    = parameters[1]
            number  = parameters[2]
        return name == "select" and text == "select" and number == 12

    @test(save=False)
    def insert_or_update(self):
        return self.database.insert(self.table,parameters=self.parameters,update=True)
