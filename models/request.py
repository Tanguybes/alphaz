import requests
from alphaz.config.config import AlphaConfig
from alphaz.utils.logger import AlphaLogger

class AlphaRequest():
    config: AlphaConfig = None
    host = None

    def __init__(self,config: AlphaConfig,log=None,logger_root=None):
        self.config = config
        self.host   = self.config.get('host')

        if log is None:
            logger_root = 'logs' if logger_root is None else logger_root
            log      = AlphaLogger(type(self).__name__,type(self).__name__.lower(),root=logger_root)

        super().__init__()

    def get_url(self,route):
        if route[0] != '/':
            route = '/' + route
        ssl = self.config.get('ssl')
        prefix = 'https://'
        if ssl is None or not ssl:
            prefix = 'http://'
        return prefix + self.host + route

    def post(self,route,data={}):
        try:
            response    = requests.post(self.get_url(route), data=data, verify=False)
            return str(response.text)
        except Exception as ex:
            print("ERROR",ex)
            return None

    def get(self,route,data={}):
        try:
            response    = requests.get(self.get_url(route), params=data, verify=False)
            return str(response.text)
        except Exception as ex:
            print("ERROR",ex)
            return None