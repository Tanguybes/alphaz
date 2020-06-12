import mysql.connector, inspect, os
from ...libs.oracle_lib import Connection 
from ...libs.sql_lib import NumpyMySQLConverter 

from collections.abc import MutableMapping

from sqlalchemy import create_engine, update
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask_sqlalchemy import SQLAlchemy

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

    def keys(self):
        return list(super().keys())

class AlphaDatabaseNew(SQLAlchemy):
    log = None
    db_type = None

    def __init__(self,*args,log=None,db_type=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.db_type = db_type
        self.log = log

    def test(self):
        try:
            self.engine.execute("SELECT 1")
            return True
        except Exception as ex:
            print('ex:',ex)
            return False

    def execute_query(self,query,values=None,close_cnx=True):
        if self.db_type == 'sqlite':
            query = query.replace('%s','?')

        # redirect to get if select
        select = query.strip().upper()[:6] == 'SELECT'
        if select:
            return self.get(query,values,unique=False)

        try:
            self.engine.execute(query, values)
            return True
        except Exception as err:
            self.log.error(err)
            return False

    def get_query_results(self,query,values,unique=False,close_cnx=True,log=None):
        if self.db_type == 'sqlite':
            query       = query.replace('%s','?')

        if log is None: log = self.log

        rows        = []
        try:
            #values          = [x for x in values]
            #print('  >>>',query,values)
            resultproxy     = self.engine.execute(query, values)   
            results         = [] 
            for rowproxy in resultproxy:
                if hasattr(rowproxy,'items'):
                    columns     = {column: value for column, value in rowproxy.items()}
                else:
                    columns     = [x for x in rowproxy]
                results.append(columns)

            if not unique:
                rows        = [Row(x) for x in results]
            else:
                rows        = [value[0] if not hasattr(value,'keys') else list(value.values())[0] for value in results]
        except Exception as err:
            stack           = inspect.stack()
            parentframe     = stack[1]
            module          = inspect.getmodule(parentframe[0])
            root            = os.path.abspath(module.__file__).replace(module.__file__,'')
            error_message = 'In file {} line {}:\n {} \n\n {}'.format(parentframe.filename,parentframe.lineno,'\n'.join(parentframe.code_context),err)
            if self.log is not None:
                self.log.error(error_message)
            #print(parentframe.frame)
            #function    = parentframe.function
            #index       = parentframe.index
        return rows

    def insert(self,model,values={},commit=True):
        values_update = self.get_values(model,values,{})
        return self.add(model,parameters=values_update,commit=commit)

    def add(self,obj,parameters=None,commit=True):
        if parameters is not None:
            parameters  = {x if not '.' in str(x) else str(x).split('.')[-1]:y for x,y in parameters.items()}
            obj         = obj(**parameters)
        if type(obj) == list:
            self.session.add_all(obj)
        else:
            tr = self.session.add(obj)

        if commit: 
            self.commit()
        return obj

    def commit(self):
        self.session.commit()

    def delete_obj(self):
        self.session.delete(obj)
        if commit: self.commit()

    def delete(self,model,filters={},commit=True):
        obj = self.select(model,filters=filters,first=True,json=False)

        if obj is not None:
            self.session.delete(obj)
            if commit: self.commit()
            return True
        return False

    def get_filtered_query(self,model,filters=None):
        query     = model.query

        if filters is not None:
            filter_unique, filter_in = {}, {}

            for key, value in filters.items():
                if type(key) == str:
                    key = getattr(model,key)
                
                if type(value) != list:
                    filter_unique[key] = value
                else:
                    filter_in[key] = value

            if len(filter_unique) != 0:
                for key, value in filter_unique.items():
                    query     = query.filter(key==value)
            if len(filter_in) != 0:
                for key, value in filter_in.items():
                    query     = query.filter(key.in_(value))
        return query 

    def select(self,model,filters=None,first=False,json=True,distinct=None,unique=None,count=False):
        #model_name = inspect.getmro(model)[0].__name__

        query     = self.get_filtered_query(model,filters=filters)

        if distinct is not None:
            query = query.distinct(distinct)

        if count:
            return query.count()

        if not unique:
            results = query.all() if not first else query.first()
        else:
            results = query.all(unique)  if not first else query.first(unique)

        if not json:
            return results

        results_json = {}
        if hasattr(model,"schema"):
            schema          = model.get_schema()
            structures      = schema(many=True) if not first else schema()
            results_json    = structures.dump(results)
        else:
            self.log.error('Missing schema for model <%s>'%str(model.__name__))
        return results_json

    def update(self,model,values={},filters={}):
        query           = self.get_filtered_query(model,filters=filters)

        values_update   = self.get_values(model,values,filters)

        print('\n%s'%model)
        for k, v in values_update.items():
            print(' u {:20} > {}'.format(str(k),v))
        query.update(values_update)

        self.commit()

    def get_values(self,model,values,filters={}):
        values_update = {}
        for key, value in values.items():
            if hasattr(model,key) and not key in filters:
                if type(key) == str:
                    values_update[model.__dict__[key]] = value
                else:
                    values_update[key] = value
        return values_update

class AlphaDatabase():
    cnx             = None
    database_type   = None
    cursor          = None
    path            = None
    cnx_str         = None

    def __init__(self,user,password,host,name=None,port=None,sid=None,database_type='mysql',log=None,path=None):
        self.log            = log
        self.database_type  = database_type
        self.user           = user
        self.password       = password
        self.host           = host
        self.name           = name
        self.port           = port
        self.sid            = sid
        self.path           = path

    def test(self):
        query   = "SHOW TABLES;"
        cnx     = self.get_cnx()
        if cnx is None:
            return False
        results = self.get_query_results(query,None)
        return len(results) != 0

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
            stack           = inspect.stack()
            parentframe     = stack[1]
            module          = inspect.getmodule(parentframe[0])
            root            = os.path.abspath(module.__file__).replace(module.__file__,'')
            error_message = 'In file {} line {}:\n {} \n\n {}'.format(parentframe.filename,parentframe.lineno,'\n'.join(parentframe.code_context),err)
            if self.log is not None:
                self.log.error(error_message)
            #print(parentframe.frame)
            #function    = parentframe.function
            #index       = parentframe.index
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