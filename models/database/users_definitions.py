
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import (
    Table,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    DateTime,
    UniqueConstraint,
    Float,
    BLOB,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.sqltypes import Boolean
from marshmallow import Schema, fields

from .models import (
    AlphaTable,
    AlphaTableId,
    AlphaColumn,
    AlphaFloat,
    AlphaInteger,
    AlphaTableIdUpdateDate,
    AlphaTableUpdateDate,
)

import datetime, inspect, ast

from core import core

db = core.get_database()
ma = core.ma

BIND = "users"
class UserSession(db.Model, AlphaTable):
    __bind_key__ = BIND
    __tablename__ = "user_session"

    user_id = AlphaColumn(Integer, primary_key=True)
    token = AlphaColumn(String(255))
    ip = AlphaColumn(String(50))
    expire = AlphaColumn(DateTime)

class User(db.Model, AlphaTableId):
    __bind_key__ = BIND
    __tablename__ = "user"

    username = AlphaColumn(String(30), primary_key=True)
    mail = AlphaColumn(String(40))
    password = AlphaColumn(String(100))
    pass_reset_token = AlphaColumn(String(100))
    pass_reset_token_exp = AlphaColumn(DateTime)
    telegram_id = AlphaColumn(String(100))
    role = AlphaColumn(Integer)
    expire = AlphaColumn(DateTime)
    date_registred = AlphaColumn(DateTime)
    last_activity = AlphaColumn(DateTime, onupdate=datetime.datetime.now())
    registration_token = AlphaColumn(String(100))
    registration_code = AlphaColumn(String(255))

class UserRole(db.Model, AlphaTableIdUpdateDate):
    __bind_key__ = BIND
    __tablename__ = "user_role"

    user_id = AlphaColumn(Integer, ForeignKey("user.id"), nullable=False, primary_key=True)
    user = relationship(
        "User",
        backref=backref(__tablename__ + "s", lazy=True, cascade="all, delete-orphan"),
    )

    role_id = AlphaColumn(Integer, ForeignKey("role.id"), nullable=False)
    role = relationship(
        "Role",
        backref=backref(__tablename__ + "s", lazy=True, cascade="all, delete-orphan"),
    )

    activated = AlphaColumn(Boolean, default=True)

class Role(db.Model, AlphaTableIdUpdateDate):
    __bind_key__ = BIND
    __tablename__ = "role"

    name = AlphaColumn(String(200), primary_key=True)
    description = AlphaColumn(Text)
    activated = AlphaColumn(Boolean, default=True)

class RolePermission(db.Model, AlphaTableIdUpdateDate):
    __bind_key__ = BIND
    __tablename__ = "role_permission"

    role_id = AlphaColumn(Integer, ForeignKey("role.id"), nullable=False, primary_key=True)
    role = relationship(
        "Role",
        backref=backref(__tablename__ + "s", lazy=True, cascade="all, delete-orphan"),
    )

    permission_id = AlphaColumn(Integer, ForeignKey("permission.id"), nullable=False, primary_key=True)
    permission = relationship(
        "Permission",
        backref=backref(__tablename__ + "s", lazy=True, cascade="all, delete-orphan"),
    )

    activated = AlphaColumn(Boolean, default=True)

class Permission(db.Model, AlphaTableIdUpdateDate):
    __bind_key__ = BIND
    __tablename__ = "permission"

    key = AlphaColumn(String(200), primary_key=True)
    description = AlphaColumn(Text)
    activated = AlphaColumn(Boolean, default=True)

class Notification(db.Model, AlphaTableIdUpdateDate):
    __bind_key__ = BIND
    __tablename__ = "notification"

    user_id = AlphaColumn(Integer, ForeignKey("user.id"), nullable=False, primary_key=True)
    user = relationship(
        "User",
        backref=backref(__tablename__ + "s", lazy=True, cascade="all, delete-orphan"),
    )

    user_from = AlphaColumn(Integer, nullable=False, primary_key=True)

    element_type = AlphaColumn(String(30))
    element_action = AlphaColumn(String(20))
    element_id = AlphaColumn(Integer)