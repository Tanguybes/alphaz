'''
Created on 25 mars 2019

@author: Aurele Durand
'''
import datetime 
import pandas as pd
import numpy as np

from ...libs import user_lib

from ...utils.decorators import overrides

from flask import jsonify, request
from flask.json import JSONEncoder

def datetime_to_str(o):
    return str(o.strftime("%Y-%m-%d %H:%M:%S"))

def object_to_panda(o):
    return o.to_json(orient='index')

def object_decode(o):
    return o.decode('utf-8')

class AlphaJSONEncoder(JSONEncoder):
    rules = {}

    def __init__(self, *args, **kwargs):
        super(AlphaJSONEncoder, self).__init__(*args, **kwargs)

        self.rules[np.int64]            = int
        self.rules[datetime.datetime]   = datetime_to_str
        self.rules[pd.DataFrame]        = object_to_panda
        self.rules[bytes]               = object_decode

    def default(self, o): # pylint: disable=E0202
        try:
            for key_type, fct in self.rules.items():
                if isinstance(o, key_type):
                    returned_value = fct(o)
                    return returned_value
            iterable = iter(o)
        except TypeError as err:
            print('ERROR:',err)
        else:
            return list(iterable)
        return JSONEncoder.default(self, o=o)

