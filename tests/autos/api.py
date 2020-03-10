
from alphaz.utils.api import api
from alphaz.models.tests import Test
import requests

class API_tests(Test):
    strategy        = None
    ref_strategy    = None

    def __init__(self):
        api.init(config_path='../../api')
        
        super().__init__()
        
    def test_api_up(self):
        filters     = {"name": "testing" }}

        url         = api.get_url() + '/test'
        response    = requests.post(url, json=filters)
        return True