# import mysql.connector
import inspect, os, re, itertools
import typing

import numpy as np

# from ...libs.oracle_lib import Connection

from pymysql.err import IntegrityError

from sqlalchemy import inspect as inspect_sqlalchemy
from sqlalchemy import update, create_engine, event
from sqlalchemy.orm import (
    relationships,
    scoped_session,
    sessionmaker,
    Session,
    load_only,
    RelationshipProperty,
    ColumnProperty,
)
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import or_, and_, all_
from sqlalchemy.sql.elements import BinaryExpression, Null
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
from ...libs import dict_lib, py_lib
from ...models.main import AlphaException
from .operators import Operators


def get_conditions_from_dict(values: dict, model, optional: bool = False):
    conditions = []
    for key, value in values.items():
        if type(key) == str:
            key = getattr(model, key)

        if type(value) == set:
            value = list(value)
        elif type(value) == dict:
            for k, v in value.items():
                if optional and v is None:
                    continue
                
                if Operators.EQUAL.equals(k) or Operators.ASIGN.equals(k):
                    conditions.append(key == v)
                elif Operators.DIFFERENT.equals(k) or Operators.NOT.equals(k):
                    conditions.append(key != v)
                elif Operators.LIKE.equals(k):
                    conditions.append(key.like(v))
                elif Operators.NOT_LIKE.equals(k):
                    conditions.append(~key.like(v))
                elif Operators.ILIKE.equals(k):
                    conditions.append(key.ilike(v))
                elif Operators.NOT_ILIKE.equals(k):
                    conditions.append(~key.ilike(v))
                elif Operators.SUPERIOR.equals(k):
                    conditions.append(key > v)
                elif Operators.INFERIOR.equals(k):
                    conditions.append(key < v)
                elif Operators.SUPERIOR_OR_EQUAL.equals(k):
                    conditions.append(key >= v)
                elif Operators.INFERIOR_OR_EQUAL.equals(k):
                    conditions.append(key <= v)
                elif Operators.NOT_IN.equals(k):
                    conditions.append(key.notin_(v))
                elif Operators.IN.equals(k):
                    conditions.append(key.in_(v))
        elif type(value) == list and value is not None:
            conditions.append(key.in_(value))
        elif not (optional and value is None):
            conditions.append(key == value)
    return conditions


def get_filters(filters, model, optional: bool = False):
    if filters is None:
        return []
    if type(filters) == set:
        filters = list(filters)
    elif type(filters) == dict:
        filters = [{x: y} for x, y in filters.items()]

    if type(filters) == dict:
        filters = get_conditions_from_dict(filters, model, optional=optional)
    elif type(filters) != list:
        filters = [filters]

    conditions = []
    for filter_c in filters:
        if type(filter_c) == dict:
            for cc in get_conditions_from_dict(filter_c, model, optional=optional):
                conditions.append(cc)
        elif not optional or (
            optional
            and _not_null_sqlaclhemy(filter_c.right)
            and _not_null_sqlaclhemy(filter_c.left)
        ):
            conditions.append(filter_c)

    return conditions


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


def _not_null_sqlaclhemy(element):
    return str(element).upper() != "NULL"


class AlphaDatabaseCore(SQLAlchemy):
    def __init__(
        self,
        *args,
        name: str = None,
        log: AlphaLogger = None,
        config=None,
        timeout: int = None,
        main: bool = False,
        **kwargs,
    ):
        self.db_type: str = config["type"]
        #cnx = config["cnx"]

        """if type(cnx) == dict:
            cnx = py_lib.filter_kwargs(create_engine, kwargs=cnx)"""
        #engine = create_engine(cnx)
        #event.listen(engine, "before_cursor_execute", add_own_encoders)
        #self._engine = engine

        engine_options = config["engine_options"] if "engine_options" in config else {}
        session_options = (
            config["session_options"] if "session_options" in config else {}
        )
        self.autocommit = (
            "autocommit" in session_options and session_options["autocommit"]
        )
        super().__init__(
            *args,
            engine_options=engine_options,
            session_options=session_options,
            **kwargs,
        )

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

    def to_json(self):
        return py_lib.get_attributes(self)

    def test(self, bind:str=None, close=False):
        """[Test the connection]

        Returns:
            [type]: [description]
        """
        output = False
        query = "SELECT 1"
        if self.db_type == "oracle":
            query = "SELECT 1 from dual"

        try:
            self.get_engine(bind=bind).execute(query)
            if not self.autocommit:
                self.session.commit()
            output = True
        except Exception as ex:
            if self.log:
                self.log.error("ex:", ex=ex)
            if not self.autocommit:
                self.session.rollback()
        finally:
            if close:
                self.session.close()
        return output

    def _get_filtered_query(
        self,
        model,
        filters=None,
        optional_filters=None,
        columns=None,
        likes=None,
        sup=None,
    ):
        query = model.query

        if columns is not None:
            ccs = []
            for column in columns:
                """if type(column) != str:
                    ccs.append(column.key)
                else:
                    ccs.append(column)"""
                if type(column) == str and hasattr(model, column):
                    ccs.append(getattr(model, column))
                else:
                    ccs.append(column)
            query = query.with_entities(*ccs)
            # query = query.options(load_only(*columns))
            # query = query.add_columns(*ccs)

        filters = get_filters(filters, model)
        optional_filters = get_filters(optional_filters, model, optional=True)
        filters = filters + optional_filters

        if filters is not None and len(filters) != 0:
            query = query.filter(and_(*filters))
        return query


class AlphaDatabase(AlphaDatabaseCore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def drop(self, table_model):
        table_model.__table__.drop(self.get_engine())

    def truncate(self, table_model, bind=None):
        self.execute(f"truncate table {table_model.__tablename__}", bind=bind)

    def execute(self, query, values=None, commit=True, bind:str=None, close=False):
        return self.execute_query(query, values, commit=commit, bind=bind, close=close)

    def execute_many_query(self, query, values=None, commit=True, bind:str=None, close=False):
        return self.execute_query(query, values, multi=True, bind=bind, commit=commit)

    def execute_query(
        self,
        query,
        values={},
        multi: bool = False,
        commit: bool = True,
        bind: str = None,
        close: bool = False,
    ) -> bool:
        if self.db_type == "sqlite":
            query = query.replace("%s", "?")

        # redirect to get if select
        select = query.strip().upper()[:6] == "SELECT"
        if select:
            return self.get_query_results(query, values, unique=False, bind=bind, close=close)

        """session = self.get_engine().connect()
        trans = session.begin()"""

        try:
            if multi:
                for value in values:
                    if value is not None:
                        self.get_engine(bind=bind).execute(query, value)
                    self.get_engine(bind=bind).execute(query)
            else:
                if values is not None:
                    self.get_engine(bind=bind).execute(query, values)
                else:
                    self.get_engine(bind=bind).execute(query)
            self.query_str = get_compiled_query(query).replace("\n", "")
            if commit and not self.autocommit:
                self.commit()
            if close:
                self.session.close()
            return True
        except Exception as ex:
            self.log.error(ex)
            return False

    def get(self, query, values=None, unique=False, bind:str=None, log=None):
        return self.get_query_results(query, values=values, unique=unique, bind=bind, log=log)

    def get_query_results(
        self, query, values=None, unique=False, log=None, bind= None, close=False
    ):
        session = self.get_engine(self.app, bind)

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
                            query = query.replace(
                                ":%s" % list(val.keys())[0], ":p%s" % i, 1
                            )
                            dict_values["p%s" % i] = list(val.values())[0]
                        else:
                            query = query.replace("?", ":p%s" % i, 1)
                            dict_values["p%s" % i] = val
                    values = dict_values

                resultproxy = session.execute(query, values, bind=bind)
            else:
                resultproxy = session.execute(query, bind=bind)
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
            self.query_str = get_compiled_query(query).replace("\n", "")
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

    def get_blocked_queries(self, bind:str=None):
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
                        trs = self.get_query_results(query % matchs_thread[0], bind=bind)
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
        self, model, parameters=None, commit:bool=True, test:bool=False, update:bool=False, flush:bool=True, close:bool=False
    ) -> object:
        if test:
            self.log.info(f"Insert {model} with values {parameters}")
            return None

        obj = model
        if parameters is not None:
            if type(parameters) != dict:
                self.log.error("<parameters must be of type <dict>")
                return None
            parameters = {
                x if not "." in str(x) else str(x).split(".")[-1]: y
                for x, y in parameters.items()
            }
            obj = model(**parameters)

        if type(obj) == list:
            self.session.add_all(obj)
        else:
            if not update:
                self.session.add(obj)
            else:
                self.session.merge(obj)

        if commit and not self.autocommit:
            self.commit()
        elif flush:
            self.session.flush()
        if close:
            self.session.close()
        return obj

    def upsert(self, model, rows, bind=None):
        if type(rows) != list:
            rows = [rows]
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
                unique = tuple(
                    [
                        const,
                    ]
                    + [getattr(row, col.name) for col in const.columns]
                )
                if unique in seen:
                    return None
                seen.add(unique)

            return row

        rows = list(filter(None, (handle_foreignkeys_constraints(row) for row in rows)))
        self.session.execute(stmt, rows, bind=bind)

    def commit(self, close=False, session=None):
        if self.autocommit:
            return True
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
            return self.commit(close=close, session=session)
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

    def ensure(self, table_name: str, bind=None, drop: bool = False):
        inspector = Inspector.from_engine(self.get_engine(bind=bind))
        tables = inspector.get_table_names()
        if not table_name.lower() in tables:
            request_model = core.get_table(self, bind, table_name)

            self.log.info(f"Creating <{table_name}> table in <{bind}> database")
            try:
                request_model.__table__.create(self.get_engine(bind=bind))
            except Exception as ex:
                if drop:
                    self.log.info(
                        f"Drop <{table_name}> table in <{bind}> database"
                    )
                    request_model.__table__.drop(self.get_engine(bind=bind))
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
                request_model.__table__.create(self.get_engine(bind=bind))
            except Exception as ex:
                if drop:
                    self.log.info('Drop <%s> table in <%s> database'%(table_name,self.name))
                    request_model.__table__.drop(self.get_engine(bind=bind))
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
        optional_filters: list = None,
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
        schema=None,
        relationship=True,
        disabled_relationships: typing.List[str] = None,
        page:int=None,
        per_page:int=100
    ):
        # model_name = inspect.getmro(model)[0].__name__
        # if self.db_type == "mysql": self.test(close=False)
        disabled_relationships = disabled_relationships or []
        disabled_relationships = [x if type(x) is str else (x.key if hasattr(x,"key") else '') for x in disabled_relationships]

        attributes = {}
        for key, col in dict(model.__dict__).items():
            if not hasattr(col, "prop"):
                continue
            
            binary_expression = type(col.expression) is BinaryExpression
            column_property = isinstance(col.prop, ColumnProperty)

            if not relationship and (column_property and not binary_expression):
                attributes[key] = col

            #! TOTO: modify
            """if disabled_relationships:
                if (column_property or isinstance(col.prop, RelationshipProperty)) and not binary_expression and key not in disabled_relationships:
                    attributes[key] = col"""

        if len(attributes) != 0:
            columns = attributes.values() if columns is None else columns.extend(attributes.values())

        if unique and (
            type(unique) == InstrumentedAttribute or type(unique) == str
        ):  # TODO: upgrade
            columns = [unique]
            distinct = True
            json = True
        elif unique:
            raise AlphaException(
                "Parameter or <unique> must be of type <InstrumentedAttribute> or <str>"
            )

        query = self._get_filtered_query(
            model, filters=filters, optional_filters=optional_filters, columns=columns
        )

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

        return self.select_query(query, model=model, first=first, json=json, unique=unique, count=count, limit=limit, close=close, 
        flush=flush, schema=schema, relationship=relationship, disabled_relationships=disabled_relationships, page=page,per_page=per_page)

    def select_query(self, query, model=None, first: bool = False, json: bool = False, unique: InstrumentedAttribute = None, 
    count: bool = False, limit: int = None, close=False, flush=False, 
    schema=None,relationship=True, disabled_relationships: typing.List[str] = None,         page:int=None,
        per_page:int=100):

        if page is not None:
            full_count = query.count()
            query = query.limit(per_page).offset(page*per_page)
            
        elif limit is not None:
            query = query.limit(limit)

        if count:
            results = query.count()
            self.query_str = get_compiled_query(query).replace("\n", "")
            self.log.debug(self.query_str)
            return results

        try:
            results = query.all() if not first else query.first()
        except Exception as ex:
            self.query_str = get_compiled_query(query).replace("\n", "")
            self.log.error(f'non valid query "{self.query_str}"', ex=ex)
            query.session.close()
            raise ex
            # raise AlphaException('non_valid_query',get_compiled_query(query),str(ex)))
        if close:
            query.session.close()
        if flush:
            query.session.flush()
        if disabled_relationships:
            json = True
        if not json:
            self.query_str = get_compiled_query(query).replace("\n", "")
            self.log.debug(self.query_str, level=2)
            return results if not page else (results, full_count)

        results_json = {}
        if schema is None:
            schema = get_schema(
                model,
                relationship=relationship,
                disabled_relationships=disabled_relationships,
            )

        structures = schema(many=True) if not first else schema()
        results_json = structures.dump(results)

        self.query_str = get_compiled_query(query).replace("\n", "")
        self.log.debug(self.query_str, level=2)

        if unique:
            if type(unique) == str:
                if not first:
                    return (
                        [] if len(results_json) == 0 else [x[unique] for x in results_json]
                    )
                else: 
                    return results_json[unique]  if not page else (results_json, full_count)
            else:
                if not first:
                    return (
                        []
                        if len(results_json) == 0
                        else [x[unique.key] for x in results_json]
                    )
                else:
                    return results_json[unique.key]  if not page else (results_json, full_count)
        """if disabled_relationships and not json:
            if type(results_json) == dict:
                results_json = model(**results_json)
            elif type(results_json) == list:
                results_json = [model(**x) for x in results_json]"""
        return results_json  if not page else (results_json, full_count)

    def update(
        self,
        model,
        values={},
        filters=None,
        fetch: bool = True,
        commit: bool = True,
        close: bool = False,
        not_none: bool = False,
    ) -> bool:
        if type(model) != list:
            models = [model]
            values_list = [values]
        else:
            models = model
            values_list = values
        size_values = len(values)

        for i, model in enumerate(models):
            if i < size_values:
                values = values_list[i]

            if hasattr(model, "metadata"):
                if filters is None and size_values == 0:
                    self.session.merge(model)
                    continue
                if filters is None:
                    filters = []
                attributes = model._sa_class_manager.local_attrs
                if len(filters) == 0:
                    for attribute in attributes:
                        col = getattr(model, attribute)
                        val = (
                            values[attribute]
                            if attribute in values
                            else (values[col] if col in values else None)
                        )
                        if (
                            hasattr(col.comparator, "primary_key")
                            and col.comparator.primary_key
                            and val is not None
                        ):
                            filters.append(col == val)

                filters = get_filters(filters, model)
                rows = self.select(model, filters=filters)
                if len(rows) == 0:
                    self.log.error(
                        f"Cannot find any entry for model {model} and values"
                    )
                    return False
                for row in rows:
                    for key, value in values.items():
                        if not_none and value is None:
                            continue
                        if type(key) == str:
                            setattr(row, key, value)
                        else:
                            setattr(row, key.key, value)
                    self.session.merge(row)
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
