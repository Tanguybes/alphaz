import mysql.connector
from ..libs.oracle_lib import Connection 
from ..libs.sql_lib import NumpyMySQLConverter 

class AlphaDatabase():
    cnx             = None
    database_type   = None

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

    def test(self):
        query   = "SHOW TABLES;"
        results = self.get_query_results(query,None)
        return len(results) != 0

    def get_query_results(self,query,values,unique=False,close_cnx=True):
        self.get_cnx()
        cursor = self.cnx.cursor(dictionary=not unique)

        rows    = []
        try:
            cursor.execute(query, values)        
            columns = cursor.description
            results = cursor.fetchall()
                
            #rows = [{columns[index][0]:column for index, column in enumerate(value)} for value in results]

            if not unique:
                rows = results
            else:
                rows = [value[0] for value in results]
            cursor.close()
            if close_cnx:
                self.cnx.close()
        except mysql.connector.Error as err:
            if self.log is not None:
                self.log.error(err)
        return rows

    def execute_query(self,query,values,close_cnx=True,log=None):
        self.get_cnx()
        try:
            cursor = self.cnx.cursor()

            cursor.execute(query, values)
            self.cnx.commit()
            cursor.close()
            if close_cnx:
                self.cnx.close()
            return True
        except mysql.connector.Error as err:
            if self.log is not None:
                self.log.error(err)
            return False
        
    def execute_many_query(self,query,values,close_cnx=True):
        self.get_cnx()
        cursor = self.cnx.cursor()

        cursor.executemany(query, values)
        self.cnx.commit()
        cursor.close()
        if close_cnx:
            self.cnx.close()