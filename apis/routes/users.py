from flask import request

from ...utils.api import route, Parameter
from ...models.main import AlphaException
from .. import users

from core import core

api = core.api


@route(
    "/register",
    methods=["POST"],
    parameters=[
        Parameter("mail", required=True),
        Parameter("username", required=True),
        Parameter("password", required=True),
        Parameter("password_confirmation", required=True),
    ],
)
def register():
    if api.get_logged_user() is not None:
        raise AlphaException("logged")
    users.try_register_user(**api.get_parameters())


@route(
    "/register/validation",
    methods=["GET"],
    parameters=[Parameter("tmp_token", required=True)],
)
def register_validation():
    if api.get_logged_user() is not None:
        raise AlphaException("logged")
    users.confirm_user_registration(**api.get_parameters())


# LOGIN
@route(
    "/auth",
    methods=["POST"],
    parameters=[
        Parameter("username", required=True),
        Parameter("password", required=True),
    ],
)
def login():
    return users.try_login(**api.get_parameters())


@route(
    "/password/lost",
    methods=["POST"],
    parameters=[
        Parameter("username", required=False),
        Parameter("mail", required=False),
    ],
)
def password_lost():
    if api.get_logged_user() is not None:
        raise AlphaException("logged")

    username = api["username"]
    mail = api.get["mail"]

    if username is None and mail is None:
        raise AlphaException("inputs")

    users.ask_password_reset(username if mail is None else mail)


@route(
    "/password/reset",
    methods=["GET", "POST"],
    parameters=[
        Parameter("tmp_token", required=True),
        Parameter("password", required=True),
        Parameter("password_confirmation", required=True),
    ],
)
def password_reset_validation():
    if api.get_logged_user() is not None:
        raise AlphaException("logged")
    users.confirm_user_password_reset(**api.get_parameters())


@route("/logout", cache=False, logged=False, methods=["GET", "POST"])
def logout():
    users.logout(token)


@route(
    "/profile/password",
    logged=True,
    methods=["POST"],
    parameters=[
        Parameter("password", required=True),
        Parameter("password_confirmation", required=True),
    ],
)
def reset_user_password():
    users.try_reset_password(**api.get_parameters())
