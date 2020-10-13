from . import sql_lib, secure_lib

from ..models.database import main_definitions as defs

def get_user_data_by_usernamePassword(db,username, password_attempt,log=None): 
    results  = db.select(defs.User,filters=[defs.User.username==username],json=True)

    for user in results:
        user_id         = user['id']
        hash_saved      = user['password']
        valid           = secure_lib.compare_passwords(password_attempt,hash_saved)

        if valid:
            return get_user_data_by_id(db, user_id)
    return None

def get_user_data_by_mailPassword(db,mail, password_attempt,log=None):
    results  = db.select(defs.User,filters=[defs.User.mail==mail],json=True)

    for user in results:
        user_id         = user['id']
        hash_saved      = user['password']
        valid           = secure_lib.compare_passwords(password_attempt,hash_saved)

        if valid:
            return get_user_data_by_id(db, user_id)
    return None

def get_user_data_FromLogin(db,login, password,log=None):
    user_mail       = get_user_data_by_mailPassword(db,login, password,log=log)
    user_username   = get_user_data_by_usernamePassword(db,login, password,log=log)
    if user_mail is not None:
        return user_mail
    if user_username is not None:
        return user_username
    return None

def get_user_data(db, value, column,log=None):
    ''' Get the user role associated with given column'''
    results  = db.select(defs.User,filters=[defs.User.__dict__[column]==value],json=True)
    if len(results) != 0:
        return results[0]
    return {}

def get_user_data_by_id(db, user_id,log=None):
    return get_user_data(db, user_id, "id")
   
def get_user_data_by_logged_token(db, token,log=None):
    return get_user_data(db, token, "token")
    
def get_user_data_by_registration_token(db, token,log=None):
    return get_user_data(db, token, "registration_token")
    
def get_user_data_by_password_reset_token(db, token,log=None):
    return get_user_data(db, token, "password_reset_token")
        
def get_user_data_by_mail(db, mail,log=None):
    return get_user_data(db, mail, "mail")
    
def get_user_data_by_username(db, username,log=None):
    return get_user_data(db, username, "username")
      
def get_user_data_by_telegram_id(db, telegram_id,log=None):
    return get_user_data(db, telegram_id, "telegram_id")

def update_users(db):
    ''' Update all users '''
    # Connect to db
    
    # Set expired states if needed
    query = "UPDATE user SET role = 0 WHERE expire <= UTC_TIMESTAMP();"
    db.execute_query(query,None)
    
    # Set expired states if needed
    query = "UPDATE user SET password_reset_token = 'consumed' WHERE password_reset_token_expire <= UTC_TIMESTAMP();"
    db.execute_query(query,None)
    
    # Remove non activated in time accounts
    query = "DELETE FROM user WHERE role = -1 AND date_registred + INTERVAL 15 MINUTE > UTC_TIMESTAMP();"
    db.execute_query(query,None)
    
    # Remove expired sessions
    query = "DELETE FROM user_session WHERE expire <= UTC_TIMESTAMP();"
    db.execute_query(query,None)
                 
def is_valid_mail(db,email): #TODO: update
    results     = db.select(defs.MailingList,filters=[defs.MailingList.email==email],json=True)
    valid       = len([x['email'] for x in results]) != 0
    return valid

def get_all_address_mails(db):
    results     = db.select(defs.MailingList,distinct=defs.MailingList.email,json=True)
    emails      = list(set([x['email'] for x in results]))
    return emails