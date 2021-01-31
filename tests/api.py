from core import core

from alphaz.utils.api import api
from alphaz.models.tests import AlphaTest, test

import requests, os

from alphaz.utils.api import api

log = core.get_logger('tests')

class API_tests(AlphaTest):
    def __init__(self):
        super().__init__()

    def get_url(self,route):
        url         = api.get_url(local=True) + route 
        return url

    def post(self,data,route):
        url = self.get_url(route)
        try:
            response    = requests.post(url, data=data, verify=False)
            return str(response.text)
        except Exception as ex:
            print("ERROR",ex)
            return None

    def get(self,data,route):
        url = self.get_url(route)
        try:
            response    = requests.get(url, params=data, verify=False)
            return str(response.text)
        except Exception as ex:
            print("ERROR",ex)
            return None

    @test(save=False)
    def api_up(self):
        key         = "testing"
        data        = {"value": key,"reset_cache":True}
        response    = self.get(data=data,route='/test')
        return response is not None and key in response
