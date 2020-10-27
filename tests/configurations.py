from ..models.tests import test, AlphaTest
from ..libs import config_lib

DB = core.get_database()

class ConfigConstants(AlphaTest):
    def __init__(self):
        self.constant_name = 'test'
        config_lib.set_db_constant(DB,self.constant_name,0)
        pass

    @test(stop=True)
    def is_db_constants():
        config_lib.is_db_constants(DB,self.constant_name)

    @test(stop=True)
    def get_db_constants(self):
        return len(config_lib.get_db_constants(DB)) != 0
        
    @test()
    def get_db_constant(self):
        return config_lib.get_db_constant(DB,self.constant_name) == 0

    @test()
    def set_db_constant(self):
        config_lib.set_db_constant(DB,self.constant_name,1)
        return config_lib.get_db_constant(DB,self.constant_name) == 1

class ConfigParameters(AlphaTest):
    def __init__(self):
        self.parameter_name = 'test'
        config_lib.set_db_parameter(DB,self.parameter_name,0)
        pass

    @test(stop=True)
    def is_db_parameters():
        config_lib.is_db_parameters(DB,self.parameter_name)

    @test(stop=True)
    def get_db_parameters(self):
        return len(config_lib.get_db_parameters(DB)) != 0
        
    @test()
    def get_db_parameter(self):
        return config_lib.get_db_parameter(DB,self.parameter_name) == 0

    @test()
    def set_db_parameter(self):
        config_lib.set_db_parameter(DB,self.parameter_name,1)
        return config_lib.get_db_parameter(DB,self.parameter_name) == 1