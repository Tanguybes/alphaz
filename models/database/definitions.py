from sqlalchemy.ext.automap import automap_base
from sqlalchemy import Table, Column, ForeignKey, Integer, String, Text, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr

from .models import AlphaModelId, AlphaColumn

import datetime, inspect

from core import core

db = core.get_database()
ma = core.ma

class Test(db.Model,AlphaModelId):
    __tablename__ = 'test'

    name            = AlphaColumn(String(30))
    text            = AlphaColumn(String(300))
    number          = AlphaColumn(Integer)
    date            = AlphaColumn(DateTime)
    update          = AlphaColumn(DateTime,default=datetime.datetime.utcnow(),
        onupdate=datetime.datetime.utcnow())

class User(db.Model,AlphaModelId):
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
    last_activity               = AlphaColumn(DateTime,
        onupdate=datetime.datetime.utcnow())
    registration_token          = AlphaColumn(String(100))
    registration_code           = AlphaColumn(String(255))

class Log(db.Model,AlphaModelId):
    __tablename__   = 'log'

    type            = AlphaColumn(String(30))
    origin          = AlphaColumn(String(30))
    message         = AlphaColumn(Text)
    stack           = AlphaColumn(Text)
    date            = AlphaColumn(DateTime)

class ProcesseLog(db.Model,AlphaModelId):
    __tablename__   = 'processe_log'

    uuid            = AlphaColumn(String(36))
    name            = AlphaColumn(String(20))
    parameters      = AlphaColumn(String(100))
    status          = AlphaColumn(String(5))
    update_date     = AlphaColumn(DateTime)

class UserSession(db.Model,AlphaModelId):
    __tablename__   = 'user_session'

    user_id         = AlphaColumn(Integer)
    token           = AlphaColumn(String(255))
    ip              = AlphaColumn(String(50))
    expire          = AlphaColumn(DateTime)

class MailHistory(db.Model,AlphaModelId):
    __tablename__   = 'mail_history'

    uuid            = AlphaColumn(String(50))
    mail_type       = AlphaColumn(String(250))
    parameters      = AlphaColumn(String(200))
    parameters_full = AlphaColumn(String(500))
    date            = AlphaColumn(DateTime)

class MailBlacklist(db.Model,AlphaModelId):
    __tablename__   = 'mail_blacklist'
    __table_args__  = (
        UniqueConstraint('mail', 'mail_type', name='unique_component_commit'),
    )

    mail            = AlphaColumn(String(50))
    mail_type       = AlphaColumn(String(20))
