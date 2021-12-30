import os, sys, warnings
import typing
from types import ModuleType
from typing import List, Dict

with warnings.catch_warnings():
    from flask_marshmallow import Marshmallow
from flask_sqlalchemy import DefaultMeta
from sqlalchemy.ext.declarative.clsregistry import _ModuleMarker

from ....models.main import AlphaClass
from ....models.logger import AlphaLogger
from ....libs import io_lib, flask_lib

from ....models.config import AlphaConfig
from ....models import database as database_models
from ....models.main import AlphaException
from ...api import AlphaFlask

from ...database.structure import AlphaDatabase

from ....utils.tasks import start_celery

import alphaz


def _get_relative_path(file: str, level=0, add_to_path=True):
    if level == 0:
        root = os.path.dirname(file)
    else:
        root = os.sep.join(os.path.dirname(file).split(os.sep)[:-level])
    if add_to_path:
        sys.path.append(root)
    return root


class AlphaCore(AlphaClass):
    instance = None

    def __init__(self, file: str, level: int = 0, *args, **kwargs):
        super().__init__(log=None)

        self.root: str = _get_relative_path(file, level=level)
        self.config: AlphaConfig = None

        self.loggers: Dict[str, AlphaLogger] = {}
        self.initiated: bool = False
        self.databases: dict = {}

        self.ma: Marshmallow = None
        self._db: AlphaDatabase = None
        self.api: AlphaFlask = None

        self.models_sources: List[str] = []
        self.__models_source_loaded: bool = False

        configuration = (
            None if not "ALPHA_CONF" in os.environ else os.environ["ALPHA_CONF"].lower().strip()
        )
        self.configuration: str = configuration
        self.configuration_name: str = configuration

        self.config: AlphaConfig = AlphaConfig(
            "config", root=self.root, configuration=configuration, core=self
        )

        self.log = self.config.get_logger("main")

    @property
    def db(self):
        self.prepare_api(self.configuration)
        return self._db
       
    def check_databases(self):
        if self.configuration == "local":
            self.prepare_api(self.configuration)
            self.load_models_sources()
            for db in self.databases.values():
                db.create_all()

    def set_configuration(self, configuration_name):
        if configuration_name is None and self.config.configuration is not None:
            configuration_name = self.config.configuration

        self.config.set_configuration(configuration_name)
        self.configuration = configuration_name
        self.configuration_name = configuration_name

    def prepare_api(self, configuration):
        if self.api is not None:
            return

        self.set_configuration(configuration)

        template_path = alphaz.__file__.replace("__init__.py", "") + "templates"
        self.api = AlphaFlask(
            __name__,
            template_folder=template_path,
            static_folder=template_path,
            root_path=template_path,
        )

        self.ma = self.api.ma

        # Cnx
        db_cnx = self.config.db_cnx

        if db_cnx is None:
            self.error(
                "Databases are not configurated in config file %s"
                % self.config.filepath
            )
            exit()

        if not "main" in db_cnx:
            self.config.show()
            self.config.error("Missing <main> database configuration")
            exit()

        # bind = not "NO_BIND" in os.environ or not "Y" in str(os.environ["NO_BIND"]).upper()
        # if bind:
        self.api.set_databases(db_cnx)

        # databases
        db_logger = self.config.get_logger("database")
        if db_logger is None:
            db_logger = self.config.get_logger("main")

        """for name, cf in db_cnx.items():
            log = self.config.get_logger(cf["logger"]) if "logger" in cf else db_logger
            self.databases[name] = AlphaDatabase(
                self.api, name=name, config=cf, log=log, main=cf == db_cnx["main"]
            )"""
        self._db = AlphaDatabase(self.api, name="main", main= True, 
        log = db_logger,
        config={"type":"oracle"})

        # configuration
        self.api.log = self.get_logger("api")
        self.api.log_requests = self.get_logger("http")

        api_root = self.config.get("api_root")
        self.api.set_config(
            name="api",
            configuration=self.configuration,
            root=api_root if api_root is not None else self.root,
        )
        self.api.db = self._db

        """# ensure tests
        self.db.ensure("tests", drop=True)
        self.db.ensure("files_process")"""

    def get_database(self, name=None) -> AlphaDatabase:
        self.prepare_api(self.configuration)

        if name is None or name == "main":
            return self._db

        if name == "users" and "users" not in self.databases:
            return self._db
        return self._db

        if name in self.databases:
            return self.databases[name]

        return self.config.get_database(name)

    def get_logger(self, *args, **kwargs) -> AlphaLogger:
        self._check_configuration()
        return self.config.get_logger(*args, **kwargs)

    def _check_configuration(self):
        if self.config is None:
            self.set_configuration(None)
            if self.config is None:
                print("ERROR: Configuration need to be initialized")
                exit()

    def get_table(self, schema: str, table: str):
        db = self.get_database(schema)
        registered_classes: List[typing.Union[DefaultMeta, _ModuleMarker]] = [
            x for x in db.Model._decl_class_registry.values()
        ]
        registered_models: Dict[str, DefaultMeta] = {
            x.__tablename__: x for x in registered_classes if isinstance(x, DefaultMeta)
        }

        if not table in registered_models:
            raise AlphaException("cannot_find_table", parameters={"table": table})
        return registered_models[table]

    def create_table(self, schema: str, table_name: str):
        # modules = flask_lib.get_definitions_modules(self.models_sources, log=self.log)
        founds = []
        for module in database_models.__dict__.values():
            if not isinstance(module, ModuleType):
                continue

            for obj in module.__dict__.values():
                if not hasattr(obj, "__tablename__"):
                    continue
                if obj.__tablename__.lower() == table_name.lower():
                    founds.append(obj)
            # table_object = self.get_table(schema, table_name)

        if len(founds) != 1:
            founds = [
                x
                for x in founds
                if not hasattr(obj, "__bind_key__")
                or (
                    hasattr(obj, "__bind_key__")
                    and schema.lower() == obj.__bind_key__.lower()
                )
            ]
        if len(founds) == 1:
            dbs = [y for x, y in self.databases.items() if x.lower() == schema.lower()]
            if len(dbs) == 1:
                founds[0].__table__.create(dbs[0].engine)

    def drop_table(self, schema: str, table_name: str):
        db = self.get_database(schema)
        table_object = self.get_table(schema, table_name)
        table_object.__table__.drop(db.engine)

    def load_models_sources(self):
        if self.__models_source_loaded:
            return

        self.models_sources = self.config.get("directories/database_models")
        if not self.models_sources:
            self.log.error(
                f"Missing <directories/database_models> entry in configuration {self.conf.filepath}"
            )
            exit()

        self.log.info(f"Getting models definitions from {self.models_sources}")
        modules = flask_lib.get_definitions_modules(self.models_sources, log=self.log)
