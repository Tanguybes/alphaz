from . import sql_lib, secure_lib

from ..models.database import main_definitions as defs
from ..models.database.users_definitions import User, UserSession

from core import core

DB = core.get_database("users")


def __get_user_data_by_identifier_and_password(
    identifier, password_attempt, identifier_type="username"
):
    filters = (
        [User.username == identifier]
        if identifier_type.lower() == "username"
        else [User.mail == identifier]
    )
    results = DB.select(User, filters=filters, json=True)

    for user in results:
        user_id = user["id"]
        if secure_lib.compare_passwords(password_attempt, user["password"]):
            return get_user_data_by_id(user_id)
    return None


def get_user_data_by_username_and_password(username, password_attempt):
    """Get user data from database by username.

    Args:
        mail ([type]): [description]
        password_attempt ([type]): [description]

    Returns:
        [type]: [description]
    """
    return __get_user_data_by_identifier_and_password(
        identifier=username,
        password_attempt=password_attempt,
        identifier_type="username",
    )


def get_user_data_by_mail_and_password(mail, password_attempt):
    """Get user data from database by mail.

    Args:
        mail ([type]): [description]
        password_attempt ([type]): [description]

    Returns:
        [type]: [description]
    """
    return __get_user_data_by_identifier_and_password(
        identifier=mail, password_attempt=password_attempt, identifier_type="mail"
    )


def get_user_data_from_login(login, password):
    """Get user data from database either by mail or username.

    Args:
        login ([type]): [description]
        password ([type]): [description]

    Returns:
        [type]: [description]
    """
    user_mail = __get_user_data_by_identifier_and_password(
        login, password, identifier_type="mail"
    )
    user_username = __get_user_data_by_identifier_and_password(
        login, password, identifier_type="username"
    )
    if user_mail is not None:
        return user_mail
    if user_username is not None:
        return user_username
    return None


def __get_user_data(value, column):
    """Get the user role associated with given column."""
    return DB.select(
        User, filters=[User.__dict__[column] == value], first=True, json=True
    )


def get_user_data_by_id(user_id):
    return __get_user_data(user_id, "id")


def get_user_data_by_logged_token(token):
    return __get_user_data(token, "token")


def get_user_data_by_registration_token(token):
    return __get_user_data(token, "registration_token")


def get_user_data_by_password_reset_token(token):
    return __get_user_data(token, "password_reset_token")


def get_user_data_by_mail(mail):
    return __get_user_data(mail, "mail")


def get_user_data_by_username(username):
    return __get_user_data(username, "username")


def get_user_data_by_telegram_id(telegram_id):
    return __get_user_data(telegram_id, "telegram_id")


def update_users():
    """Update all users."""

    # Set expired states if needed
    query = "UPDATE user SET role = 0 WHERE expire <= UTC_TIMESTAMP();"
    DB.execute_query(query, None)

    # Set expired states if needed
    query = "UPDATE user SET password_reset_token = 'consumed' WHERE password_reset_token_expire <= UTC_TIMESTAMP();"
    DB.execute_query(query, None)

    # Remove non activated in time accounts
    query = "DELETE FROM user WHERE role = -1 AND date_registred + INTERVAL 15 MINUTE > UTC_TIMESTAMP();"
    DB.execute_query(query, None)

    # Remove expired sessions
    query = "DELETE FROM user_session WHERE expire <= UTC_TIMESTAMP();"
    DB.execute_query(query, None)


def is_valid_mail(email):  # TODO: update
    return (
        DB.select(
            defs.MailingList,
            filters=[defs.MailingList.email == email],
            distinct=defs.MailingList.email,
            unique=defs.MailingList.email,
            first=True,
        )
        != None
    )


def get_all_address_mails():
    return DB.select(
        defs.MailingList, distinct=defs.MailingList.email, unique=defs.MailingList.email
    )

