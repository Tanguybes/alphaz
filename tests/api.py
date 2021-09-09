from core import core

from alphaz.utils.api import api
from alphaz.models.tests import AlphaTest, test

from alphaz.libs import api_lib
from alphaz.utils.api import api
from alphaz.models.api import ApiMethods
from alphaz.models.main import AlphaException

log = core.get_logger('tests')

class API(AlphaTest):
    def __init__(self):
        super().__init__()

    def get_api_data(self, route:str, params:dict={}, method:ApiMethods=ApiMethods.GET, data_only:bool=True):
        return api_lib.get_api_data(api.get_url(local=True) + route,params=params, method=method, data_only=data_only)

    @test(save=False)
    def api_up(self):
        key         = "testing"
        response    = self.get_api_data(route='/test/parameters',params={"value": key,"reset_cache":True})
        return "value" in response and response["value"] == "testing"

    @test(save=False)   
    def cache(self):
        key         = "testing"
        response    = self.get_api_data(route='/test/parameters',params={"value": key,"reset_cache":True})
        if not "value" in response:
            raise AlphaException("Empty response")

        uuid = response["uuid"]
        response    = self.get_api_data(route='/test/parameters',params={"value": key,"reset_cache":False})
        if not "value" in response:
            raise AlphaException("Empty response")
        return uuid == response["uuid"]

    @test(save=False)   
    def reset_cache(self):
        key         = "testing"
        response    = self.get_api_data(route='/test/parameters',params={"value": key,"reset_cache":True})
        if not "value" in response:
            raise AlphaException("Empty response")

        uuid = response["uuid"]
        response    = self.get_api_data(route='/test/parameters',params={"value": key,"reset_cache":True})
        if not "value" in response:
            raise AlphaException("Empty response")
        return uuid != response["uuid"]