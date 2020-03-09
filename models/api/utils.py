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
    def default(self, obj):
        try:
            if isinstance(obj, np.int64):
                return int(obj)
            if isinstance(obj, datetime.datetime):
                strDate = str(obj.strftime("%Y-%m-%d %H:%M:%S"))
                return strDate
            if isinstance(obj, pd.DataFrame):
                strObj = obj.to_json(orient='index')
                return strObj
            if isinstance(obj, bytes):
                strObj = obj.decode('utf-8')
                return strObj
            iterable = iter(obj)
        except TypeError as err:
            print('ERROR:',err)
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)