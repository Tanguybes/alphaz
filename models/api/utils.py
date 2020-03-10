'''
Created on 25 mars 2019

@author: Aurele Durand
'''
import datetime 
import pandas as pd
import numpy as np

from ...libs import user_lib

from flask import jsonify, request
from flask.json import JSONEncoder

# HELPER TO REPLACE DATE OBJETS (or others) IN STR FORMAT BY DEFAULT - MAGIC
class CustomJSONEncoder(JSONEncoder):
    def default(self, o):
        try:
            if isinstance(o, np.int64):
                return int(o)
            if isinstance(o, datetime.datetime):
                strDate = str(o.strftime("%Y-%m-%d %H:%M:%S"))
                return strDate
            if isinstance(o, pd.DataFrame):
                strObj = o.to_json(orient='index')
                return strObj
            if isinstance(o, bytes):
                strObj = o.decode('utf-8')
                return strObj
            iterable = iter(o)
        except TypeError as err:
            print('ERROR:',err)
        else:
            return list(iterable)
        return JSONEncoder.default(self, o)