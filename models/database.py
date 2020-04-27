import mysql.connector
from ..libs.oracle_lib import Connection 
from ..libs.sql_lib import NumpyMySQLConverter 

from collections.abc import MutableMapping

class Row(MutableMapping):
    """A dictionary that applies an arbitrary key-altering
       function before accessing the keys"""

    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key):
        if not key in list(self.keys()) and type(key) == int:
            key = list(self.keys())[key]
        return self.store[self.__keytransform__(key)]

    def __setitem__(self, key, value):
        self.store[self.__keytransform__(key)] = value

    def __delitem__(self, key):
        del self.store[self.__keytransform__(key)]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __keytransform__(self, key):
        return key

class AlphaDatabase():
    cnx             = None
    database_type   = None
    cursor          = None

    def __init__(self,user,password,host,name=None,port=None,sid=None,database_type='mysql',log=None):
        self.log            = log
        self.database_type  = database_type
        self.user           = user
        self.password       = password
        self.host           = host
        self.name           = name
        self.port           = port
        self.sid            = sid

    def get_cnx(self):
        cnx = None
        if self.database_type == 'mysql':
            try:
                if self.port is not None:
                    self.log.debug('Connecting to host=%s, database=%s, user=%s, port=%s'%(self.host,self.name,self.user,self.port))
                    cnx         = mysql.connector.connect(user=self.user, password=self.password, host=self.host, database=self.name,port=self.port)
                else:
                    cnx         = mysql.connector.connect(user=self.user, password=self.password, host=self.host, database=self.name)        
                cnx.set_converter_class(NumpyMySQLConverter)
            except Exception as ex:
                if self.log is not None:
                    self.log.error(str(ex))
        elif self.database_type == 'oracle':
            cnx = Connection(self.host, self.port, self.sid,self.user,self.password)
        else:
            if self.log is not None:
                self.log.error('Database type not recognized')
        self.cnx = cnx
        return self.cnx

    def test(self):
        query   = "SHOW TABLES;"
        results = self.get_query_results(query,None)
        return len(results) != 0

    def get(self,query,values,unique=False,close_cnx=True):
        return self.get_query_results(query,values,unique=unique,close_cnx=close_cnx)

    def get_query_results(self,query,values,unique=False,close_cnx=True,log=None):
        if log is None: log = self.log

        self.get_cnx()
        self.cursor = self.cnx.cursor(dictionary=not unique)

        rows    = []
        try:
            self.cursor.execute(query, values)        
            columns = self.cursor.description
            results = self.cursor.fetchall()
                
            #rows = [{columns[index][0]:column for index, column in enumerate(value)} for value in results]

            if not unique:
                rows = [Row(x) for x in results]
            else:
                rows = [value[0] for value in results]

            self.cursor.close()

            if close_cnx:
                self.cnx.close()
        except mysql.connector.Error as err:
            if self.log is not None:
                self.log.error(err)
        return rows

    def execute(self,query,values=None,close_cnx=True,log=None):
        return self.execute_query(query,values,close_cnx,log)

    def execute_query(self,query,values=None,close_cnx=True,log=None):
        if log is None: log = self.log

        # redirect to get if select
        select = query.strip().upper()[:6] == 'SELECT'
        if select:
            return self.get(query,values,unique=False,close_cnx=True)

        self.get_cnx()
        try:
            self.cursor = self.cnx.cursor()

            self.cursor.execute(query, values)
            self.cnx.commit()
            self.cursor.close()
            if close_cnx:
                self.cnx.close()
            return True
        except mysql.connector.Error as err:
            if log is not None:
                log.error(err)
            return False

    def delete(self,table:str,parameters: dict,close_cnx=True,log=None):
        query  = "delete from " + table
        query += " where " + ' and '.join(["`"+key+"` = %s" for key in parameters.keys()])
        return self.execute(query,values=list(parameters.values()),close_cnx=close_cnx,log=log)

    def insert(self,table:str , parameters: dict,update=False,close_cnx=True,log=None):
        query  = "insert into `" + table + "` (%s) "% ','.join(["`%s`"%x for x in parameters.keys()])
        query += " values (%s) " % ','.join(["%s" for x in parameters.values()])

        if update:
            query += " on duplicate key update "
            query += ",".join(["`%s`=values(`%s`)"%(x,x) for x in parameters.keys()])
        return self.execute(query,values=list(parameters.values()),close_cnx=close_cnx,log=log)

    def select(self,table:str, columns,unique=False):
        if unique and len(columns) != 1:
            if self.log is not None:
                self.log.error('Cannot select one row only because you asked more: selecting all')
                unique = False

        query = "select " + ','.join(['`%s`'%x for x in columns]) + " from " + table
        return self.get(query, values=None,unique=unique)
        
    def execute_many_query(self,query,values,close_cnx=True,log=None):
        if log is None: log = self.log

        self.get_cnx()
        self.cursor = self.cnx.cursor()

        self.cursor.executemany(query, values)
        self.cnx.commit()
        self.cursor.close()
        if close_cnx:
            self.cnx.close()

    def close(self):
        self.cnx.close()