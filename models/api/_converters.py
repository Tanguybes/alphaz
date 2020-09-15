'''
Created on 25 mars 2019

@author: Aurele Durand
'''
import datetime 
import pandas as pd
import numpy as np

from flask import jsonify, request
from flask.json import JSONEncoder

from flask_sqlalchemy.model import DefaultMeta

from ...utils.decorators import overrides

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


def jsonify_database_models(model: DefaultMeta,first=False):
    """Convert a database model structure to json

    Args:
        model (DefaultMeta): database mode structure
        first (bool, optional): [description]. Defaults to False.

    Returns:
        [type]: [description]
    """
    schema          = model.get_schema()
    structures      = schema(many=True) if not first else schema()
    results_json    = structures.dump([model])
    return results_json


def jsonify_data(data):
    """Convert any data to a json structure

    Args:
        data ([type]): data to convert

    Returns:
        [type]: data converted as a json structure
    """
    if type(data) == list:
        result = [jsonify_data(x) for x in data]
    elif type(data) == dict:
        result = {jsonify_data(x):jsonify_data(y) for x,y in data.items()}
    else:
        result = data
        if hasattr(data,"schema"):
            print('schema',data)
            result = jsonify_database_models(data)
    return result
