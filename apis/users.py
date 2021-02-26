import datetime, jwt
from ..libs import user_lib, sql_lib, secure_lib

from ..models.database.users_definitions import User, UserSession

from ..models.main import AlphaException

from core import core

from flask import request

API = core.api
DB = core.get_database("users")

LOGIN_MODE = core.api.conf.get("auth/mode")

# Serve for registration
def try_register_user(mail, username, password, password_confirmation, validation=True):
    userByMail = user_lib.get_user_data_by_mail(mail)
    userByUsername = user_lib.get_user_data_by_username(username)

    if "id" in userByMail or "id" in userByUsername:
        if ("id" in userByMail and userByMail["role"] < 0) or (
            "id" in userByUsername and userByUsername["role"] < 0
        ):
            raise AlphaException("account_not_validated")
        raise AlphaException("account_duplicated")

    if password != password_confirmation:
        raise AlphaException("password_missmatch")

    '''mail_valid = validate_email(mail)
    if not mail_valid:
        return "mail_format"'''

    '''if not password_check_format(password):
        return "password_format"'''

    password_hashed = secure_lib.secure_password(password)

    # ADD CHECKS FOR LENGHT OF USERNAME/MAIL!!

    # Generate token
    token = secure_lib.get_token()

    parameters = {"token": token, "name": username, "mail": mail}

    if validation and not API.send_mail(
        mail_config="registration", parameters_list=[parameters], db=DB
    ):
        raise AlphaException("sending")
    DB.add(
        User(
            username=username,
            mail=mail,
            password=password_hashed,
            role=-1 if validation else 1,
            date_registred=datetime.datetime.now(),
            last_activity=datetime.datetime.now(),
            registration_token=token,
        )
    )


def ask_password_reset(username_or_mail):
    user_by_mail = user_lib.get_user_data_by_mail(username_or_mail)
    user_by_username = user_lib.get_user_data_by_username(username_or_mail)

    if len(user_by_mail.keys()) == 0 and len(user_by_username.keys()) == 0:
        raise AlphaException("unknown_inputs")

    if "id" not in user_by_mail and "id" not in user_by_username:
        raise AlphaException("unknown_inputs")

    user_data = user_by_mail if "id" in user_by_mail else user_by_username

    # Generate token
    token = secure_lib.get_token()

    query = "UPDATE user SET password_reset_token = %s, password_reset_token_expire = UTC_TIMESTAMP() + INTERVAL 20 MINUTE WHERE id = %s;"
    values = (
        token,
        user_data["id"],
    )

    if not DB.execute_query(query, values):
        raise AlphaException("sql_error")

    # MAIL
    parameters = {}
    parameters["mail"] = user_data["mail"]
    parameters["token"] = token
    parameters["username"] = user_data["username"]
    parameters["name"] = user_data["username"]

    mail_sent = API.send_mail(
        mail_config="password_reset", parameters_list=[parameters], db=DB
    )


def confirm_user_registration(token):
    if "consumed" in token:
        raise AlphaException("invalid_token")
    user_data = user_lib.get_user_data_by_registration_token(DB, token)

    if len(user_data) == 0:
        AlphaException("not_found")

    if "id" in user_data:
        # Set Role to 0 and revoke token
        user = DB.select(
            User, filters={"id": user_data["id"]}, first=True, json=False
        )
        if user is None:
            raise AlphaException("error")
        user.role = 0
        user.registration_token = "consumed"
        DB.commit()

        valid = True
        if not valid:
            raise AlphaException("error")


def try_login(username, password):
    if API.get_logged_user() is not None:
        raise AlphaException("user_already_logged")
    user_data = user_lib.get_user_data_from_login(username, password)
    if LOGIN_MODE == "ldap" and user_data is None:
        valid_ldap = True #TODO: modify
        if not valid_ldap:
            raise AlphaException("unknown_user")
        try_register_user(mail=username, username=username, password=password, password_confirmation=password, validation=False)
        user_data = user_lib.get_user_data_from_login(username, password)
    else:
        if user_data is None:
            raise AlphaException("unknown_user")

    if user_data["role"] == 0:
        raise AlphaException("account_not_validated")
    if not "JWT_SECRET_KEY" in API.config:
        raise AlphaException("Missing <JWT_SECRET_KEY> api parameter")

    # Generate token
    encoded_jwt = jwt.encode(
        {
            "username": user_data["username"],
            "id": user_data["id"],
            "time": str(datetime.datetime.now()),
        },
        API.config["JWT_SECRET_KEY"],
        algorithm="HS256",
    )
    try: #TODO: remove
        encoded_jwt = encoded_jwt.decode("ascii")
    except:
        pass

    defaults_validity = {
        "days": 7,
        "seconds": 0,
        "microseconds": 0,
        "milliseconds": 0,
        "minutes": 0,
        "hours": 0,
        "weeks": 0,
    }
    validity_config = API.conf.get("token/login/validity")
    validity_config = {
        x: y
        if (validity_config is None or not x in validity_config)
        else validity_config[x]
        for x, y in defaults_validity.items()
    }

    # Add new token session related to user
    if not DB.add_or_update(
        UserSession(
            user_id=user_data["id"],
            token=encoded_jwt,
            ip=request.remote_addr,
            expire=datetime.datetime.now() + datetime.timedelta(**validity_config),
        )
    ):
        raise AlphaException("error")

    return {
        "id": user_data["id"],
        "token": encoded_jwt,
        "valid_until": datetime.datetime.now() + datetime.timedelta(**validity_config),
    }


def confirm_user_password_reset(tmp_token, password, password_confirmation):
    if "consumed" in tmp_token:
        raise AlphaException("consumed_token")

    user_data = user_lib.get_user_data_by_password_reset_token(DB, tmp_token)
    if not "id" in user_data:
        raise AlphaException("invalid_token")

    try_reset_password(user_data, password, password_confirmation)


def try_reset_password(password, password_confirmation):
    if password != password_confirmation:
        raise AlphaException("password_missmatch")
    user_data = API.get_logged_user()

    '''if not password_check_format(password):
        return "password_format"'''
    # Set New password and revoke token
    password_hashed = secure_lib.secure_password(password)

    # Reset password
    query = "UPDATE user SET password = %s, password_reset_token = 'consumed' WHERE id = %s;"
    values = (
        password_hashed,
        user_data["id"],
    )
    valid = DB.execute_query(query, values)
    if not valid:
        raise AlphaException("reset_error")

    # Reset all sessions as password changed
    query = "DELETE FROM user_session WHERE user_id = %s;"
    values = (user_data["id"],)
    valid = DB.execute_query(query, values)
    if not valid:
        raise AlphaException("clean_error")


def logout():
    token = API.get_token()
    if token is None:
        raise AlphaException("token_not_specified")
    if not DB.delete(UserSession, filters={"token": token}):
        raise AlphaException("fail")


def get_user_dataFromToken(token):
    user_id = None
    results = DB.select(
        UserSession, filters=[UserSession.token == token], json=True
    )
    if len(results) != 0:
        user_id = results[0]["user_id"]

    if user_id is not None:
        return user_lib.get_user_data_by_id(user_id)
    return None


def try_subscribe_user(mail, nb_days, target_role):
    userByMail = user_lib.get_user_data_by_mail(mail)
    user_data = None
    if "id" in userByMail:
        if "id" in userByMail:
            user_data = userByMail
    expired_date = datetime.datetime.now() + datetime.timedelta(days=nb_days)
    if user_data is not None:
        # Reset password
        query = "UPDATE user SET role = %s, expire = %s WHERE id = %s;"
        values = (
            target_role,
            expired_date,
            user_data["id"],
        )
        valid = DB.execute_query(query, values)
        if not valid:
            AlphaException("update_error")
    AlphaException("unknow_user")
