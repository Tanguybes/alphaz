import datetime, jwt, itertools

from sqlalchemy.sql.expression import update

from sqlalchemy.sql.functions import user
from ..libs import user_lib, sql_lib, secure_lib, json_lib

from ..models.database.users_definitions import User, UserSession

from ..models.main import AlphaException

from core import core

from flask import request

API = core.api
DB = core.get_database("users")

LOG = core.get_logger("users")
LOGIN_MODE = core.api.conf.get("auth/mode")
if LOGIN_MODE == "ldap":
    import ldap

    LDAP_SERVER = API.conf.get("auth/ldap/server")
    BASE_DN = API.conf.get("auth/ldap/baseDN")
    LDAP_DATA = API.conf.get("auth/ldap/user_data")

# Serve for registration
def try_register_user(
    mail, username, password, password_confirmation, validation=True, infos=""
):
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
            infos=json_lib.jsonify_data(infos, string_output=True),
        )
    )


def update_infos(user_data, infos) -> bool:
    if type(infos) != str:
        infos = json_lib.jsonify_data(infos, string_output=True)

    infos_user = (
        json_lib.jsonify_data(user_data["infos"])
        if type(user_data["infos"]) != str
        else user_data["infos"]
    )
    if infos == infos_user:
        return True
    user_id = user_data["id"]
    return DB.update(User, values={"infos": infos}, filters=[User.id == user_id])


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
        user = DB.select(User, filters={"id": user_data["id"]}, first=True, json=False)
        if user is None:
            raise AlphaException("error")
        user.role = 0
        user.registration_token = "consumed"
        DB.commit()

        valid = True
        if not valid:
            raise AlphaException("error")


def check_credentials(username, password):
    try:
        l = ldap.initialize(LDAP_SERVER)
        l.protocol_version = ldap.VERSION3
    except Exception as ex:
        LOG.error(ex)
        return None
    searchScope = ldap.SCOPE_SUBTREE
    retrieveAttributes = None
    searchFilter = f"uid={username}"
    try:
        ldap_result_id = l.search(
            BASE_DN, searchScope, searchFilter, retrieveAttributes
        )
        result_set = []
        while 1:
            result_type, result_data = l.result(ldap_result_id, 0)
            if result_data == []:
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data)

        if (
            result_set is not None
            and result_set[0] is not None
            and result_set[0][0] is not None
            and result_set[0][0][0] is not None
        ):
            LDAP_USERNAME = result_set[0][0][0]
            LDAP_PASSWORD = password
            try:
                ldap_client = ldap.initialize(LDAP_SERVER)
                ldap_client.set_option(ldap.OPT_REFERRALS, 0)
                ldap_client.simple_bind_s(LDAP_USERNAME, LDAP_PASSWORD)
            except ldap.INVALID_CREDENTIALS:
                ldap_client.unbind()
                LOG.error("Wrong username or password")
                return None
            except ldap.SERVER_DOWN:
                LOG.error("AD server not awailable")
                return None
            ldap_client.unbind()

            return {
                x: y[0].decode() if len(y) == 1 else ([u.decode() for u in y])
                for x, y in result_set[0][0][1].items()
            }
    except Exception as ex:
        LOG.error(ex)
    return None


def try_login(username, password):
    env = core.configuration
    if API.get_logged_user() is not None:
        raise AlphaException("user_already_logged")

    if LOGIN_MODE == "ldap":
        valid_ldap = check_credentials(username, password)
        if valid_ldap is None:
            raise AlphaException("unknown_user")
        added_infos = {}
        if LDAP_DATA is not None:
            for ldap_name, name in LDAP_DATA.items():
                added_infos[name] = (
                    valid_ldap[ldap_name] if ldap_name in valid_ldap else ""
                )
        user_data = user_lib.get_user_data_from_login(username, password)
        if user_data is None:
            try_register_user(
                mail=valid_ldap["mail"],
                username=username,
                password=password,
                password_confirmation=password,
                validation=False,
                infos=added_infos,
            )
            user_data = user_lib.get_user_data_from_login(username, password)
        else:
            update_infos(user_data, added_infos)
    else:
        user_data = user_lib.get_user_data_from_login(username, password)
        if user_data is None:
            raise AlphaException("unknown_user")

    if user_data["role"] == 0:
        raise AlphaException("account_not_validated")
    if not "JWT_SECRET_KEY" in API.config:
        raise AlphaException("Missing <JWT_SECRET_KEY> api parameter")

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
    expire = datetime.datetime.now() + datetime.timedelta(**validity_config)

    # Generate token
    data_to_jwt = {"id": "id", "username": "sub", "time": "iat", "user_roles": "roles"}
    user_data["time"] = str(datetime.datetime.now())
    user_data_to_encode = {y: user_data[x] for x, y in data_to_jwt.items()}
    user_data_to_encode["exp"] = str(expire)
    user_data_to_encode["app"] = "alpha"
    user_data_to_encode["env"] = env

    encoded_jwt = jwt.encode(
        user_data_to_encode,
        API.config["JWT_SECRET_KEY"],
        algorithm="HS256",
    )
    try:  # TODO: remove
        encoded_jwt = encoded_jwt.decode("ascii")
    except Exception as ex:
        pass

    # Add new token session related to user
    if not DB.add_or_update(
        UserSession(
            user_id=user_data["id"],
            token=encoded_jwt,
            ip=request.remote_addr,
            expire=expire,
        )
    ):
        raise AlphaException("error")

    return {
        **{x: y for x, y in user_data.items() if not x in data_to_jwt},
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
    results = DB.select(UserSession, filters=[UserSession.token == token], json=True)
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
