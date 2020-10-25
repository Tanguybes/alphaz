import  sys, os, re

import pandas as pd

oracle_path = 'C:\oracle\product\instantclient_19_5'
    
def update_os():
    os.environ["PATH"] = oracle_path + "\;"+os.environ["PATH"]
    #os.environ["NLS_LANG"] = ".UTF8"

    #os.environ['ORACLE_HOME'] = oracle_path
    
import os
update_os()
#import cx_Oracle
"""
class Connection():
    conn = None
    dataset  = None
    col_names = []
    
    def __init__(self,host,port,sid,user,pwd):
        dsn_tns         = cx_Oracle.makedsn(host, port, sid)
        self.conn       = cx_Oracle.connect(user,pwd,dsn_tns)
        
    def select(self,query):
        cursor    = self.conn.cursor()
        
        cursor.execute(query)

        col_names = []
        for i in range(0, len(cursor.description)):
            col_names.append(cursor.description[i][0])
            
        group = []
        for row in cursor:
            group.append(row)

        dataset = pd.DataFrame(group,columns=col_names)
        
        self.col_names  = col_names
        self.dataset    = dataset
        return dataset

    def get_values(self,key):
        key = key.upper()
        if key in self.col_names:
            return self.dataset[key].values
        return []
        
    def close(self):
        self.conn.close()
        """
