import mysql.connector
from .oracle_lib import Connection 

class NumpyMySQLConverter(mysql.connector.conversion.MySQLConverter):
    """ A mysql.connector Converter that handles Numpy types """

    def _float32_to_mysql(self, value):
        return float(value)

    def _float64_to_mysql(self, value):
        return float(value)

    def _int32_to_mysql(self, value):
        return int(value)

    def _int64_to_mysql(self, value):
        return int(value)

def get_connection_from_infos(user,password,host,name=None,port=None,sid=None,database_type='mysql'):
    cnx = None
    if database_type == 'mysql':
        print('heyyyy')
        try:
            if port is not None:
                cnx         = mysql.connector.connect(user=user, password=password, host=host, database=name,port=port)
            else:
                cnx         = mysql.connector.connect(user=user, password=password, host=host, database=name)        
            cnx.set_converter_class(NumpyMySQLConverter)
        except Exception as ex:
            print(str(ex))
    elif database_type == 'oracle':
        cnx = Connection(host, port, sid,user,password)
    else:
        print('Database type not recognized')
    return cnx

def get_query_results(cnx,query,values,unique=False,close_cnx=True,log=None):
    cursor = cnx.cursor(dictionary=not unique)

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
            cnx.close()
    except mysql.connector.Error as err:
        if log is not None:
            log.error(err)
    return rows

def execute_query(cnx,query,values,close_cnx=True,log=None):
    try:
        cursor = cnx.cursor()

        cursor.execute(query, values)
        cnx.commit()
        cursor.close()
        if close_cnx:
            cnx.close()
        return True
    except mysql.connector.Error as err:
        if log is not None:
            print('   err',err)
            log.error(err)
        return False
    
def execute_many_query(cnx,query,values,close_cnx=True):
    cursor = cnx.cursor()

    cursor.executemany(query, values)
    cnx.commit()
    cursor.close()
    if close_cnx:
        cnx.close()