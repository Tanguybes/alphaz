import mysql.connector, inspect, os
from ...libs.oracle_lib import Connection 
from ...libs.sql_lib import NumpyMySQLConverter 

from collections.abc import MutableMapping

from sqlalchemy import update
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import or_, and_, all_
from flask_sqlalchemy import SQLAlchemy

from ...models.main import AlphaException

def get_compiled_query(query):
    if hasattr(query,'statement'):
        full_query_str = query.statement.compile(compile_kwargs={"literal_binds": True})
    else:
        full_query_str = str(query)
    full_query_str = full_query_str if not hasattr('full_query_str','string') else full_query_str.string
    return full_query_str

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

    def __repr__(self):
        return self.store.__repr__()

    def show(self):
        for k, v in self.store.items():
            print('   {:20} {}'.format(k,v))

    def keys(self):
        return list(super().keys())

class AlphaDatabaseCore(SQLAlchemy):
    def __init__(self,*args,name=None,log=None,config=None,timeout=None,**kwargs):
        timeout = 5
        engine_options = {}
        if timeout is not None:
            engine_options={ 'connect_args': { 'connect_timeout': 5 }, 'pool_recycle':5} # TODO: modify
            """
                                 'pool_size' : 10,
                                 'pool_recycle':120,
                                 'pool_pre_ping': True
            """

        super().__init__(*args,engine_options=engine_options,**kwargs)

        self.name       = name

        self.config     = config
        self.db_type    = config['type']
        self.log        = log 

    def test(self):
        """[Test the connection]

        Returns:
            [type]: [description]
        """
        query = "SELECT 1"
        if self.db_type == "oracle":
            query = "SELECT 1 FROM DUAL"
        try:
            self.engine.execute(query)
            return True
        except Exception as ex:
            if self.log: self.log.error('ex:',ex)
            return False

    def _get_filtered_query(self,model,filters=None,likes=None,sup=None):
        query     = model.query

        if filters is not None:
            if type(filters) == list:
                query = get_filter_conditions(query,filters)
            else:
                query = get_filter(query,filters,model)
        return query 

class AlphaDatabase(AlphaDatabaseCore):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

    def drop(self,table_model):
        table_model.__table__.drop(self.engine)

    def execute_query(self,query,values=None):
        if self.db_type == 'sqlite':
            query = query.replace('%s','?')

        # redirect to get if select
        select = query.strip().upper()[:6] == 'SELECT'
        if select:
            return self.get_query_results(query,values,unique=False)
        
        try:
            self.engine.execute(query, values)
            self.query_str = get_compiled_query(query)
            return True
        except Exception as err:
            self.log.error(err)
            return False

    def get(self,query,values=None,unique=False,log=None):
        return self.get_query_results(query,values=None,unique=False,log=None)

    def get_query_results(self,query,values=None,unique=False,log=None):
        session = self.get_engine(self.app, self.name)

        if self.db_type == 'sqlite':
            query       = query.replace('%s','?')

        if log is None: log = self.log

        rows        = []
        try:
            if values is not None:
                resultproxy     = session.execute(query, values)   
            else:
                resultproxy     = session.execute(query)   
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

        #self.query_str = get_compiled_query(query)
        return rows

    def insert(self,model,values={},commit=True,test=False):
        values_update = self.get_values(model,values,{})
        return self.add(model,parameters=values_update,commit=commit,test=test)

    def insert_or_update(self,model,values={},commit=True,test=False):
        values_update = self.get_values(model,values,{})
        return self.add(model,parameters=values_update,commit=commit,test=test,update=True)

    def add_or_update(self,obj,parameters=None,commit=True,test=False,update=False):
        return self.add(obj=obj,parameters=parameters,commit=commit,test=test,update=True)

    def add(self,obj,parameters=None,commit=True,test=False,update=False):
        if test:
            self.log.info('Insert %s with values %s'%(obj,parameters))
            return None

        if parameters is not None:
            parameters  = {x if not '.' in str(x) else str(x).split('.')[-1]:y for x,y in parameters.items()}
            obj         = obj(**parameters)

        if type(obj) == list:
            self.session.add_all(obj)
        else:
            if not update:
                self.session.add(obj)
            else:
                self.session.merge(obj)

        if commit: 
            try:
                self.commit()
            except Exception as ex:
                raise AlphaException('database_insert',description=str(ex))
        return obj

    def commit(self):
        self.session.commit()

    def delete_obj(self):
        self.session.delete(obj)
        if commit: self.commit()

    def delete(self,model,filters=None,commit=True):
        obj = self.select(model,filters=filters,first=True,json=False)

        if obj is not None:
            self.session.commit()
            self.session.delete(obj)
            if commit: self.commit()
            return True
        return False

    def exist(self,model):
        try:
            instance = self.session.query(model).first()
            return True
        except:
            return False

    def select(self,model,
            filters=None,
            first=False,
            json=False,
            distinct=None,
            unique=None,
            count=False,
            order_by=None,
            group_by=None,
            limit=None,
            columns=None
        ):
        #model_name = inspect.getmro(model)[0].__name__

        query     = self._get_filtered_query(model,filters=filters)

        if distinct is not None:
            query = query.distinct(distinct) if type(distinct) != tuple else query.distinct(*distinct)

        if group_by is not None:
            query = query.group_by(group_by) if type(group_by) != tuple else query.group_by(*group_by)

        if order_by is not None:
            query = query.order_by(order_by) if type(order_by) != tuple else query.order_by(*order_by)

        if limit is not None:
            query = query.limit(limit)

        if count:
            results = query.count()
            self.query_str = get_compiled_query(query)
            return results
        
        if unique: 
            columns = [unique]
        if columns is not None:
            query = query.with_entities(*columns)
            #TODO: get column if string

        try:
                results = query.all() if not first else query.first()
        except Exception as ex:
            #self.log.error('non valid query "%s" \n%s'%(get_compiled_query(query),str(ex)))
            raise ex
            #raise AlphaException('non_valid_query',get_compiled_query(query),str(ex)))

        if not json:
            self.query_str = get_compiled_query(query)
            return results

        results_json = {}
        if hasattr(model,"schema"):
            schema          = model.get_schema()
            structures      = schema(many=True) if not first else schema()
            results_json    = structures.dump(results)
        else:
            self.log.error('Missing schema for model <%s>'%str(model.__name__))
        self.query_str      = get_compiled_query(query)

        if unique:
            return [list(x.values())[0] for x in results_json]
        return results_json

    def update(self,model,values={},filters={}):
        query           = self._get_filtered_query(model,filters=filters)
        values_update   = self.get_values(model,values,filters)
        query.update(values_update)

        self.commit()

    def get_values(self,model,values,filters={}):
        values_update = {}
        for key, value in values.items():
            if type(key) == InstrumentedAttribute and not key in filters:
                values_update[key] = value
            elif type(key) == str and hasattr(model,key) and not key in filters:
                values_update[model.__dict__[key]] = value
                    
        return values_update

def get_filter_conditions(query,filters,verbose=True):
    equals, ins, likes, sups, infs, sups_st, infs_st = {}, {}, {}, {}, {}, {}, {}
    
    conditions = []

    if type(filters) == list:
        conditions = filters

    elif type(filters_conditions) == dict:
        for filters_conditions in filters:
            for key, value in filters_conditions.items():
                if type(key) == str:
                    key = getattr(model,key)
                
                if type(value) == set: 
                    value = list(value)
                    
                if type(value) == dict:
                    for k, v in value.items():
                        if k == '==' or k == '=':               conditions.append(key == v)
                        if k == '!=' or k == '!':               conditions.append(key != v)
                        if k == '%':                            conditions.append(key.like(v))
                        if k == '!%':                           conditions.append(~key.like(v))
                        if k == '>':                            conditions.append(key > v)
                        if k == '<':                            conditions.append(key < v)
                        if k == '>=':                           conditions.append(key >= v)
                        if k == '<=':                           conditions.append(key <= v)
                        if k == '!':                            conditions.append(key != v)
                        if k == 'notin':                        conditions.append(key.notin_(v))
                        if k == 'in':                           conditions.append(key.in_(v))
                                            
                elif type(value) != list:
                    equals[key] = value
                else:
                    ins[key] = value

    for key, value in equals.items():
        conditions.append(key==value)

    for key, value in ins.items():
        conditions.append(key.in_(value))
    
    filter_cond = and_(*conditions)
    query       = query.filter(filter_cond)
    return query

def get_filter(query,filters,model,verbose=True):
    equals, ins, likes, sups, infs, sups_st, infs_st = {}, {}, {}, {}, {}, {}, {}

    for key, value in filters.items():
        if type(key) == str:
            key = getattr(model,key)
        
        if type(value) == set: 
            value = list(value)
            
        if type(value) == dict:
            for k, v in value.items():
                if k == '==' or k == '=':               query = query.filter(key == v)
                if k == '!=' or k == '!':               query = query.filter(key != v)
                if k == '%':                            query = query.filter(key.like(v))
                if k == '!%':                           query = query.filter(~key.like(v))
                if k == '>':                            query = query.filter(key > v)
                if k == '<':                            query = query.filter(key < v)
                if k == '>=':                           query = query.filter(key >= v)
                if k == '<=':                           query = query.filter(key <= v)
                if k == '!':                            query = query.filter(key != v)
                if k == 'notin':                        query = query.filter(key.notin_(v))
                if k == 'in':                           query = query.filter(key.in_(v))
                                
        elif type(value) != list:
            equals[key] = value
        else:
            ins[key] = value

    for key, value in equals.items():
        query     = query.filter(key==value)

    for key, value in ins.items():
        query     = query.filter(key.in_(value))
    return query