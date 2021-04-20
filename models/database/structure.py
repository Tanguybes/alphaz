# import mysql.connector
import inspect, os, re
import numpy as np

# from ...libs.oracle_lib import Connection

from pymysql.err import IntegrityError

from sqlalchemy import inspect as inspect_sqlalchemy
from sqlalchemy import update, create_engine, event
from sqlalchemy.orm import scoped_session, sessionmaker, Session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import or_, and_, all_
from flask_sqlalchemy import SQLAlchemy, BaseQuery
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.base import object_mapper
from sqlalchemy.orm.exc import UnmappedInstanceError

from time import sleep
import logging
from .row import Row
from .utils import get_schema

from ...models.logger import AlphaLogger
from ...libs import dict_lib
from ...models.main import AlphaException

def get_compiled_query(query):
    if hasattr(query, "statement"):
        full_query_str = query.statement.compile(compile_kwargs={"literal_binds": True})
    elif hasattr(query, "query"):
        full_query_str = query.query.statement.compile(
            compile_kwargs={"literal_binds": True}
        )
    else:
        full_query_str = str(query)
    full_query_str = (
        full_query_str
        if not hasattr(full_query_str, "string")
        else full_query_str.string
    )

    return full_query_str


def add_own_encoders(conn, cursor, query, *args):
    if hasattr(cursor.connection, "encoders"):
        cursor.connection.encoders[np.float64] = lambda value, encoders: float(value)
        cursor.connection.encoders[np.int64] = lambda value, encoders: int(value)


class RetryingQuery(BaseQuery):

    __retry_count__ = 3
    __retry_sleep_interval_sec__ = 0.5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __iter__(self):
        attempts = 0
        while True:
            attempts += 1
            try:
                return super().__iter__()
            except OperationalError as ex:
                if "Lost connection to MySQL server during query" not in str(ex):
                    print(">> Retry failed")
                    raise
                if attempts < self.__retry_count__:
                    print(">>Retry")
                    logging.debug(
                        "MySQL connection lost - sleeping for %.2f sec and will retry (attempt #%d)",
                        self.__retry_sleep_interval_sec__,
                        attempts,
                    )
                    sleep(self.__retry_sleep_interval_sec__)
                    continue
                else:
                    raise


class BaseModel:
    query_class = RetryingQuery


class AlphaDatabaseCore(SQLAlchemy):
    def __init__(
        self,
        *args,
        name: str = None,
        log: AlphaLogger = None,
        config=None,
        timeout: int = None,
        main: bool = False,
        **kwargs
    ):
        self.db_type: str = config["type"]
        if "user" in config:
            self.user: str = config["user"]
        cnx = config["cnx"]

        engine = create_engine(cnx)
        event.listen(engine, "before_cursor_execute", add_own_encoders)
        self._engine = engine
        
        engine_options = config["engine_options"] if 'engine_options' in config else {}
        session_options = config["session_options"] if 'session_options' in config else {}
        super().__init__(*args, engine_options=engine_options, session_options=session_options, **kwargs)

        """if not bind:
            session = scoped_session(sessionmaker(autocommit=False,
                                    autoflush=False,
                                    bind=engine))
            self._engine = engine
            self.Model = declarative_base()
            self.Model.query = session.query_property()
            self._session = session"""

        self.name: str = name
        self.main = main

        self.config = config
        self.log: AlphaLogger = log

        self.error = None

        self.query_str = None

    """def get_engine(self, bind=None):
        return self.db.get_engine(bind=self.name)

    def get_session(self):
        return self.db.session"""

    def test(self, close=False):
        """[Test the connection]

        Returns:
            [type]: [description]
        """
        output = False
        query = "SELECT 1"
        if self.db_type == "oracle":
            # query = "SELECT 1 FROM DUAL"
            query = "SELECT 1;"
        try:
            self._engine.execute(query)
            self.session.commit()
            output = True
        except Exception as ex:
            # if self.log: self.log.error('ex:',ex)
            self.session.rollback()
        finally:
            if close:
                self.session.close()
        return output

    def _get_filtered_query(self, model, filters=None, likes=None, sup=None):
        query = model.query

        if filters is not None:
            if type(filters) == list:
                query = get_filter_conditions(query, filters)
            else:
                query = get_filter(query, filters, model)
        return query


class AlphaDatabase(AlphaDatabaseCore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def drop(self, table_model):
        table_model.__table__.drop(self.get_engine())

    def execute(self, query, values=None, commit=True, close=False):
        return self.execute_query(query, values, commit=commit, close=close)

    def execute_many_query(self, query, values=None, commit=True, close=False):
        return self.execute_query(query, values, multi=True, commit=commit)

    def execute_query(
        self,
        query,
        values={},
        multi: bool = False,
        commit: bool = True,
        close: bool = False,
    ) -> bool:
        if self.db_type == "sqlite":
            query = query.replace("%s", "?")

        # redirect to get if select
        select = query.strip().upper()[:6] == "SELECT"
        if select:
            return self.get_query_results(query, values, unique=False, close=close)

        """session = self.get_engine().connect()
        trans = session.begin()"""

        try:
            if multi:
                for value in values:
                    self._engine.execute(query, value)
            else:
                self._engine.execute(query, values)
            self.query_str = get_compiled_query(query)
            if commit:
                self.commit()
            if close:
                self.session.close()
            return True
        except Exception as ex:
            self.log.error(ex)
            return False

    def get(self, query, values=None, unique=False, log=None):
        return self.get_query_results(query, values=values, unique=unique, log=log)

    def get_query_results(
        self, query, values=None, unique=False, log=None, close=False
    ):
        session = self.get_engine(self.app, self.name)

        if self.db_type == "sqlite":
            query = query.replace("%s", "?")

        if log is None:
            log = self.log

        rows = []
        try:
            if values is not None:
                if type(values) == list and len(values) != 0:
                    dict_values = {}
                    for i, val in enumerate(values):
                        if type(val) == dict:
                            query = query.replace(":%s"%list(val.keys())[0], ":p%s" % i, 1)
                            dict_values["p%s" % i] = list(val.values())[0]
                        else:
                            query = query.replace("?", ":p%s" % i, 1)
                            dict_values["p%s" % i] = val
                    values = dict_values

                resultproxy = session.execute(query, values)
            else:
                resultproxy = session.execute(query)
            results = []
            for rowproxy in resultproxy:
                if hasattr(rowproxy, "items"):
                    columns = {column: value for column, value in rowproxy.items()}
                else:
                    columns = [x for x in rowproxy]
                results.append(columns)

            if not unique:
                rows = [Row(x) for x in results]
            else:
                rows = [
                    value[0] if not hasattr(value, "keys") else list(value.values())[0]
                    for value in results
                ]
            self.query_str = get_compiled_query(query)
        except Exception as ex:
            if self.log is not None:
                self.log.error(ex)
            """
            except Exception as err:
                stack = inspect.stack()
                parentframe = stack[1]
                module = inspect.getmodule(parentframe[0])
                root = os.path.abspath(module.__file__).replace(module.__file__, "")
                error_message = "In file {} line {}:\n {} \n\n {}".format(
                    parentframe.filename,
                    parentframe.lineno,
                    "\n".join(parentframe.code_context),
                    err,
                )
                if self.log is not None:
                    self.log.error(error_message)
            """
        if close:
            session.close()

        return rows

    # MySQL thread id 6081, OS thread handle 0x7f475abcc700, query id 9036497 localhost 127.0.0.1 golliathdb

    def get_blocked_queries(self):
        query = """SELECT SQL_TEXT
        FROM performance_schema.events_statements_history ESH,
            performance_schema.threads T
        WHERE ESH.THREAD_ID = T.THREAD_ID
        AND ESH.SQL_TEXT IS NOT NULL
        AND T.PROCESSLIST_ID = %s
        ORDER BY ESH.EVENT_ID LIMIT 10;"""

        transaction_id = None
        result_list = self.get_engine().execute("show engine innodb status;")
        outputs = {}
        for result in list(result_list)[0]:
            for line in result.split("\n"):
                if transaction_id is not None:
                    matchs_thread = re.findall("thread id ([0-9]*),", line)
                    matchs_query = re.findall("query id ([0-9]*)", line)
                    if len(matchs_thread):
                        trs = self.get_query_results(query % matchs_thread[0])
                        outputs[int(times)] = [x["SQL_TEXT"] for x in trs]
                    transaction_id = None

                matchs_tr = re.findall(
                    "---TRANSACTION ([0-9]*), ACTIVE ([0-9]*) sec", line
                )
                if len(matchs_tr) != 0:
                    transaction_id, times = matchs_tr[0]
        outputs = dict_lib.sort_dict(outputs, reverse=True)
        return outputs

    def insert(self, model, values={}, commit=True, test=False, close=False):
        values_update = self.get_values(model, values, {})
        return self.add(
            model, parameters=values_update, commit=commit, test=test, close=close
        )

    def insert_or_update(self, model, values={}, commit=True, test=False):
        # return self.upsert(model, values)
        values_update = self.get_values(model, values, {})
        return self.add(
            model, parameters=values_update, commit=commit, test=test, update=True
        )

    def add_or_update(self, obj, parameters=None, commit=True, test=False, update=True):
        return self.add(
            obj, parameters=parameters, commit=commit, test=test, update=True
        )

    def add(
        self, model, parameters=None, commit=True, test=False, update=False, close=False
    ) -> object:
        if test:
            self.log.info("Insert %s with values %s" % (model, parameters))
            return None

        if parameters is not None:
            parameters = {
                x if not "." in str(x) else str(x).split(".")[-1]: y
                for x, y in parameters.items()
            }
            obj = model(**parameters)
        else:
            obj = model

        if type(obj) == list:
            obj_ = self.session.add_all(obj)
        else:
            if not update:
                obj_ = self.session.add(obj)
            else:
                obj_ = self.session.merge(obj)

        if commit:
            self.commit()
            """except Exception as ex:
                primaryKeyColName = inspect_sqlalchemy(obj)

                raise AlphaException("database_insert", description=str(ex))"""
        if close:
            self.session.close()
        return obj

    def upsert(self, model, rows):
        from sqlalchemy.dialects import postgresql
        from sqlalchemy import UniqueConstraint

        table = model.__table__
        stmt = postgresql.insert(table)
        primary_keys = [key.name for key in inspect_sqlalchemy(table).primary_key]
        update_dict = {c.name: c for c in stmt.excluded if not c.primary_key}

        if not update_dict:
            raise ValueError("insert_or_update resulted in an empty update_dict")

        stmt = stmt.on_conflict_do_update(index_elements=primary_keys, set_=update_dict)

        seen = set()
        foreign_keys = {
            col.name: list(col.foreign_keys)[0].column
            for col in table.columns
            if col.foreign_keys
        }
        unique_constraints = [
            c for c in table.constraints if isinstance(c, UniqueConstraint)
        ]

        def handle_foreignkeys_constraints(row):
            for c_name, c_value in foreign_keys.items():
                foreign_obj = row.pop(c_value.table.name, None)
                row[c_name] = (
                    getattr(foreign_obj, c_value.name) if foreign_obj else None
                )

            for const in unique_constraints:
                unique = tuple([const,] + [row[col.name] for col in const.columns])
                if unique in seen:
                    return None
                seen.add(unique)

            return row

        rows = list(filter(None, (handle_foreignkeys_constraints(row) for row in rows)))
        self.session.execute(stmt, rows)

    def commit(self, close=False, session=None):
        if session is None:
            session = self.session
        valid = True
        try:
            session.commit()
        except Exception as ex:
            raise ex
            self.log.error(ex=ex)
            session.rollback()
            valid = False
        finally:
            if close:
                session.close()
        return valid

    def delete_obj(self, obj, commit: bool = True, close: bool = False) -> bool:
        session = self.object_session(obj)
        session.delete(obj)
        if commit:
            return self.commit(close=close,session=session)
        return True

    def delete(
        self, model, filters=None, commit: bool = True, close: bool = False
    ) -> bool:
        objs = self.select(model, filters=filters, json=False)
        if len(objs) == 0:
            return False
        for obj in objs:
            self.delete_obj(obj, commit=False)
        if commit:
            return self.commit(close=close)
        return True

    def ensure(self, table_name: str, drop: bool = False):
        inspector = Inspector.from_engine(self._engine)
        tables = inspector.get_table_names()
        if not table_name.lower() in tables:
            request_model = core.get_table(self, self.name, table_name)

            self.log.info(
                "Creating <%s> table in <%s> database" % (table_name, self.name)
            )
            try:
                request_model.__table__.create(self._engine)
            except Exception as ex:
                if drop:
                    self.log.info(
                        "Drop <%s> table in <%s> database" % (table_name, self.name)
                    )
                    request_model.__table__.drop(self._engine)
                    self.ensure(table_name)
                else:
                    self.log.error(ex)

        """
        #if not cls.__tablename__ in cls.metadata.tables:
        #    cls.metadata.create_all()
        # ensure tests
        
        if not self.exist(request_model):
            self.log.info('Creating <%s> table in <%s> database'%(table_name,self.name))
            try:
                request_model.__table__.create(self._engine)
            except Exception as ex:
                if drop:
                    self.log.info('Drop <%s> table in <%s> database'%(table_name,self.name))
                    request_model.__table__.drop(self._engine)
                    self.ensure(table_name)
                else:
                    self.log.error(ex)
        """

    def exist(self, model):
        try:
            instance = self.session.query(model).first()
            return True
        except Exception as ex:
            self.log.error(ex=ex)
            return False

    def select(
        self,
        model,
        filters: list = None,
        first: bool = False,
        json: bool = False,
        distinct=None,
        unique: InstrumentedAttribute = None,
        count: bool = False,
        order_by=None,
        group_by=None,
        limit: int = None,
        columns: list = None,
        close=False,
        flush=False,
    ):
        # model_name = inspect.getmro(model)[0].__name__
        """if self.db_type == "mysql": self.test(close=False)"""

        query = self._get_filtered_query(model, filters=filters)
        if distinct is not None:
            query = (
                query.distinct(distinct)
                if type(distinct) != tuple
                else query.distinct(*distinct)
            )

        if group_by is not None:
            query = (
                query.group_by(group_by)
                if type(group_by) != tuple
                else query.group_by(*group_by)
            )

        if order_by is not None:
            query = (
                query.order_by(order_by)
                if type(order_by) != tuple
                else query.order_by(*order_by)
            )

        if limit is not None:
            query = query.limit(limit)

        if count:
            results = query.count()
            self.query_str = get_compiled_query(query)
            self.log.debug(self.query_str)
            return results

        if unique and (
            type(unique) == InstrumentedAttribute or type(unique) == str
        ):  # TODO: upgrade
            columns = [unique]
            json = True
        elif unique:
            self.log.error(
                "Parameter or <unique> must be of type <InstrumentedAttribute> or <str>"
            )
        if columns is not None:
            query = query.with_entities(*columns)
            # TODO: get column if string

        try:
            results = query.all() if not first else query.first()
        except Exception as ex:
            self.query_str = get_compiled_query(query)
            self.log.error('non valid query "%s" \n%s' % (self.query_str, str(ex)))
            query.session.close()
            raise ex
            # raise AlphaException('non_valid_query',get_compiled_query(query),str(ex)))
        if close:
            query.session.close()
        if flush:
            query.session.flush()

        if not json:
            self.query_str = get_compiled_query(query)
            self.log.debug(self.query_str, level=2)
            return results

        results_json = {}
        if hasattr(model, "schema"):
            schema = model.get_schema()
        else:
            self.log.error("Missing schema for model <%s>" % str(model.__name__))
            schema = get_schema(model)

        structures = schema(many=True) if not first else schema()
        results_json = structures.dump(results)

        self.query_str = get_compiled_query(query)
        self.log.debug(self.query_str, level=2)

        if unique:
            if type(results_json) == list:
                return [list(x.values())[0] for x in results_json]
            else:
                return (
                    None if len(results_json) == 0 else list(results_json.values())[0]
                )

        return results_json

    def update(
        self,
        model,
        values={},
        filters=None,
        fetch: bool = True,
        commit: bool = True,
        close: bool = False,
    ) -> bool:
        if type(model) != list:
            models = [model]
            values_list = [values]
        else:
            models = model 
            values_list = values
        size_values= len(values)
        for i, model in enumerate(models):
            if i < size_values:
                values = values_list[i]
            
            if hasattr(model, "metadata"): 
                self.session.merge(model)
            else:
                query = self._get_filtered_query(model, filters=filters)
                values_update = self.get_values(model, values, filters)
 
                if fetch:
                    query.update(values_update, synchronize_session="fetch")
                else:
                    try:
                        query.update(values_update, synchronize_session="evaluate")
                    except:
                        query.update(values_update, synchronize_session="fetch")
 
        if commit:
            return self.commit(close)
        return True

    def get_values(self, model, values, filters=None):
        values_update = {}
        for key, value in values.items():
            if type(key) == InstrumentedAttribute and not key in filters:
                values_update[key] = value
            elif type(key) == str and hasattr(model, key) and not key in filters:
                values_update[model.__dict__[key]] = value
        return values_update


def get_filter_conditions(query, filters):
    equals, ins, likes, sups, infs, sups_st, infs_st = {}, {}, {}, {}, {}, {}, {}

    conditions = []

    if type(filters) == list:
        conditions = filters

    elif type(filters_conditions) == dict:
        for filters_conditions in filters:
            for key, value in filters_conditions.items():
                if type(key) == str:
                    key = getattr(model, key)

                if type(value) == set:
                    value = list(value)

                if type(value) == dict:
                    for k, v in value.items():
                        if k == "==" or k == "=":
                            conditions.append(key == v)
                        if k == "!=" or k == "!":
                            conditions.append(key != v)
                        if k == "%":
                            conditions.append(key.like(v))
                        if k == "!%":
                            conditions.append(~key.like(v))
                        if k == ">":
                            conditions.append(key > v)
                        if k == "<":
                            conditions.append(key < v)
                        if k == ">=":
                            conditions.append(key >= v)
                        if k == "<=":
                            conditions.append(key <= v)
                        if k == "!":
                            conditions.append(key != v)
                        if k == "notin":
                            conditions.append(key.notin_(v))
                        if k == "in":
                            conditions.append(key.in_(v))

                elif type(value) != list:
                    equals[key] = value
                else:
                    ins[key] = value

    for key, value in equals.items():
        conditions.append(key == value)

    for key, value in ins.items():
        conditions.append(key.in_(value))

    filter_cond = and_(*conditions)
    query = query.filter(filter_cond)
    return query


def get_filter(query, filters, model):
    equals, ins, likes, sups, infs, sups_st, infs_st = {}, {}, {}, {}, {}, {}, {}

    for key, value in filters.items():
        if type(key) == str:
            key = getattr(model, key)

        if type(value) == set:
            value = list(value)

        if type(value) == dict:
            for k, v in value.items():
                if k == "==" or k == "=":
                    query = query.filter(key == v)
                if k == "!=" or k == "!":
                    query = query.filter(key != v)
                if k == "%":
                    query = query.filter(key.like(v))
                if k == "!%":
                    query = query.filter(~key.like(v))
                if k == ">":
                    query = query.filter(key > v)
                if k == "<":
                    query = query.filter(key < v)
                if k == ">=":
                    query = query.filter(key >= v)
                if k == "<=":
                    query = query.filter(key <= v)
                if k == "!":
                    query = query.filter(key != v)
                if k == "notin":
                    query = query.filter(key.notin_(v))
                if k == "in":
                    query = query.filter(key.in_(v))

        elif type(value) != list:
            equals[key] = value
        else:
            ins[key] = value

    for key, value in equals.items():
        query = query.filter(key == value)

    for key, value in ins.items():
        query = query.filter(key.in_(value))
    return query
