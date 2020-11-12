from sqlalchemy.ext.automap import automap_base
from sqlalchemy import Table, Column, ForeignKey, Integer, String, Text, DateTime, UniqueConstraint, Float, BLOB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship, backref

from .models import AlphaTable, AlphaTableId, AlphaColumn, AlphaFloat, AlphaInteger, AlphaTableIdUpdateDate, AlphaTableUpdateDate

import datetime, inspect, ast

from core import core

db = core.get_database()
ma = core.ma

class FilesProcess(db.Model,AlphaTableUpdateDate):
    __bind_key__        = 'main'
    __tablename__       = "files_process"
    ensure              = True

    name                = AlphaColumn(String(40),nullable=False,primary_key=True)
    key                 = AlphaColumn(String(100),nullable=False,primary_key=True)
    filename            = AlphaColumn(String(100),nullable=False,primary_key=True)
    modifiation_time    = AlphaColumn(Integer)
    filesize            = AlphaColumn(Integer)
    lifetime            = AlphaColumn(Integer)
    error               = AlphaColumn(Integer)

class Processes(db.Model,AlphaTableIdUpdateDate):
    __bind_key__        = 'main'
    __tablename__ = "processes"

    uuid = AlphaColumn(String(36))
    name = AlphaColumn(String(20))
    parameters = AlphaColumn(String(20))
    status = AlphaColumn(String(5))

    __table_args__  = (
        UniqueConstraint('name', 'parameters', name='processes_constraint'),
    )

class Logs(db.Model,AlphaTableIdUpdateDate):
    __bind_key__        = 'main'
    __tablename__ = "logs"

    type_ = AlphaColumn(String(30))
    origin = AlphaColumn(String(30))
    message = AlphaColumn(Text)
    stack = AlphaColumn(Text)

class Notification(db.Model,AlphaTableIdUpdateDate):
    __bind_key__        = 'main'
    __tablename__ = "notification"

    user = AlphaColumn(Integer, ForeignKey('user.id'),
        nullable=False)
    userObj = relationship('User',
        backref=backref(__tablename__ + "s", lazy=True,  cascade="all, delete-orphan"))

    user_from = AlphaColumn(Integer,nullable=False)

    element_type = AlphaColumn(String(30))
    element_action = AlphaColumn(String(20))
    element_id = AlphaColumn(Integer)

class Tests(db.Model,AlphaTableIdUpdateDate):
    __bind_key__        = 'main'
    __tablename__ = 'tests'

    category  = AlphaColumn(String(50))
    tests_group  = AlphaColumn(String(50))
    name  = AlphaColumn(String(50))

    status = AlphaColumn(Integer)
    start_time          = AlphaColumn(DateTime)
    end_time          = AlphaColumn(DateTime)
    elapsed  = AlphaColumn(Float)

class Request(db.Model,AlphaTable):
    __bind_key__        = 'main'
    __tablename__ = "request"

    index = AlphaColumn(Integer, primary_key=True, autoincrement=True)
    response_time = AlphaColumn(Float)
    date = AlphaColumn(DateTime)
    method = AlphaColumn(String(6))
    size = AlphaColumn(Integer)
    status_code = AlphaColumn(Integer)
    path = AlphaColumn(String(100))
    user_agent = AlphaColumn(String(200))
    remote_address = AlphaColumn(String(20))
    exception = AlphaColumn(String(500))
    referrer = AlphaColumn(String(100))
    browser = AlphaColumn(String(100))
    platform = AlphaColumn(String(20))
    mimetype = AlphaColumn(String(30))

class NewsLetter(db.Model, AlphaTableIdUpdateDate):
    __bind_key__        = 'main'
    __tablename__       = "newsletter"
    name  = AlphaColumn(String(100))
    mail  = AlphaColumn(String(50))

class Test(db.Model, AlphaTableIdUpdateDate):
    __bind_key__        = 'main'
    __tablename__       = 'test'

    name_             = AlphaColumn(String(30))
    text_             = AlphaColumn(String(300))
    number_           = AlphaColumn(Integer)
    date_             = AlphaColumn(DateTime)

class User(db.Model, AlphaTableId):
    __bind_key__        = 'main'
    __tablename__ = 'user'

    username                    = AlphaColumn(String(30))
    mail                        = AlphaColumn(String(40))
    password                    = AlphaColumn(String(100))
    password_reset_token        = AlphaColumn(String(100))
    password_reset_token_expire = AlphaColumn(DateTime)
    telegram_id                 = AlphaColumn(String(100))
    role                        = AlphaColumn(Integer)
    expire                      = AlphaColumn(DateTime)
    date_registred              = AlphaColumn(DateTime)
    last_activity               = AlphaColumn(DateTime, onupdate=datetime.datetime.now())
    registration_token          = AlphaColumn(String(100))
    registration_code           = AlphaColumn(String(255))

class Log(db.Model,AlphaTableIdUpdateDate):
    __bind_key__        = 'main'
    __tablename__   = 'log'

    type            = AlphaColumn(String(30))
    origin          = AlphaColumn(String(30))
    message         = AlphaColumn(Text)
    stack           = AlphaColumn(Text)

class ProcesseLog(db.Model,AlphaTableIdUpdateDate):
    __bind_key__        = 'main'
    __tablename__   = 'process_log'

    uuid            = AlphaColumn(String(36))
    name            = AlphaColumn(String(20))
    parameters      = AlphaColumn(String(100))
    status          = AlphaColumn(String(5))

class UserSession(db.Model,AlphaTableId):
    __bind_key__        = 'main'
    __tablename__   = 'user_session'

    user_id         = AlphaColumn(Integer)
    token           = AlphaColumn(String(255))
    ip              = AlphaColumn(String(50))
    expire          = AlphaColumn(DateTime)

class MailHistory(db.Model,AlphaTableIdUpdateDate):
    __bind_key__        = 'main'
    __tablename__   = 'mail_history'

    uuid            = AlphaColumn(String(50))
    mail_type       = AlphaColumn(String(250))
    parameters      = AlphaColumn(String(200))
    parameters_full = AlphaColumn(String(500))
    date            = AlphaColumn(DateTime)

class MailBlacklist(db.Model,AlphaTableId):
    __bind_key__        = 'main'
    __tablename__   = 'mail_blacklist'
    __table_args__  = (
        UniqueConstraint('mail', 'mail_type', name='unique_component_commit'),
    )

    mail            = AlphaColumn(String(50))
    mail_type       = AlphaColumn(String(20))

class Requests(db.Model, AlphaTableIdUpdateDate):
    __bind_key__ = "main"
    __tablename__ = "requests"

    uuid = AlphaColumn(String(100))
    process = AlphaColumn(Integer)
    message = AlphaColumn(Text)
    message_type = AlphaColumn(String(20))
    lifetime = AlphaColumn(Integer)
    creation_date = AlphaColumn(DateTime,default=datetime.datetime.now)

    def get_message(self):
        try:
            message = ast.literal_eval(self.message)
        except:
            return None

class Answers(db.Model, AlphaTableIdUpdateDate):
    __bind_key__ = "main"
    __tablename__ = "answers"

    uuid = AlphaColumn(String(100))
    process = AlphaColumn(Integer)
    message = AlphaColumn(Text)
    message_type = AlphaColumn(String(20))
    lifetime = AlphaColumn(Integer)
    creation_date = AlphaColumn(DateTime,default=datetime.datetime.now)

class Constants(db.Model,AlphaTableIdUpdateDate):
    __tablename__ = "constants"
    __bind_key__ = "main"

    name = AlphaColumn(String(30))
    value = AlphaColumn(String(100))

class Parameters(db.Model,AlphaTableIdUpdateDate):
    __tablename__ = "parameters"
    __bind_key__ = "main"

    name = AlphaColumn(String(30))
    value = AlphaColumn(BLOB)