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
        url         = api.get_url() + route
        return url

    def test_api_up(self):
        key         = "testing"
        data        = {"name": key }
        response    = self.get(data=data,route='/test')
        return response is not None and key in response


    def post(self,data,route):
        try:
            response    = requests.post(self.get_url(route), data=data, verify=False)
            return str(response.text)
        except Exception as ex:
            print("ERROR",ex)
            return None

    def get(self,data,route):
        try:
            print(self.cert)
            response    = requests.get(self.get_url(route), params=data, verify=False)
            return str(response.text)
        except Exception as ex:
            print("ERROR",ex)
            return None

    @test(save=False)
    def api_up(self):
        key         = "testing"
        data        = {"name": key }
        response    = self.get(data=data,route='/test')
        return response is not None and key in response