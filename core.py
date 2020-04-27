import os, sys

from alphaz.utils.logger import AlphaLogger
from alphaz.config.config import AlphaConfig
from alphaz.models.main.core import AlphaCore
from alphaz.models.main.singleton import singleton
from alphaz.utils.api import api

@singleton
class Core(AlphaCore):
    root            = None
    api             = None
    test_database   = None
    config          = None
    log             = None

    def __init__(self,file:str):
        super().__init__(file)
        self.root    = os.path.basename(os.path.dirname(os.path.realpath(__file__)))

        self.config  = AlphaConfig('config',filepath=self.root + os.sep + 'config')

        self.log     = self.config.get_logger('main')

        api.init(config_path=self.root + os.sep + 'api')
        self.api     = api

        self.test_database = self.config.get_database('test')
        
core = Core(__file__)
