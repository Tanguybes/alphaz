from flask import request

from ...utils.api import route, Parameter
from ...models.main import AlphaException
from .. import users

from core import core

api = core.api
db = core.db
log = core.get_logger("api")


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

    users.try_register_user(
        api,
        db,
        api.get("mail"),
        api.get("username"),
        api.get("password"),
        api.get("password_confirmation"),
    )


@route(
    "/register/validation",
    methods=["GET"],
    parameters=[Parameter("tmp_token", required=True)],
)
def register_validation():
    if api.get_logged_user() is not None:
        raise AlphaException("logged")

    users.confirm_user_registration(api, token=api.get("tmp_token"), db=db)


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
    users.try_login(
        api, db, api.get("username"), api.get("password"), request.remote_addr
    )


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

    username = api.get("username")
    mail = api.get("mail")

    if username is not None or mail is not None:
        username_or_mail = username if mail is None else mail
        users.ask_password_reset(api, username_or_mail, db=db)
    else:
        AlphaException("inputs")


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

    users.confirm_user_password_reset(
        api,
        token=api.get("tmp_token"),
        password=api.get("password"),
        password_confirmation=api.get("password_confirmation"),
        db=db,
    )


@route("/logout", cache=False, logged=False, methods=["GET", "POST"])
def logout():
    token = api.get_token()

    users.logout(api, token, db=db)


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
    user_data = api.get_logged_user()

    users.try_reset_password(
        api,
        user_data,
        api["password"],
        api["password_confirmation"],
        db=db,
        log=api.log,
    )
