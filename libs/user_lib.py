from . import sql_lib, secure_lib

def get_user_data_by_usernamePassword(db,username, password_attempt,log=None,close_cnx=True):
    query    = "SELECT id, password FROM users WHERE username = %s;"
    values   = (username,)

    

    results  = db.get_query_results(query,values,unique=False,close_cnx=False)

    print('hhhhey',results)

    for user in results:
        user_id         = user['id']
        hash_saved      = user['password']
        valid           = secure_lib.compare_passwords(password_attempt,hash_saved)

        print('   >>>',user_id,hash_saved,password_attempt,valid )
        if valid:
            return get_user_data_by_id(db, user_id,close_cnx=close_cnx)
    return None

def get_user_data_by_mailPassword(db,mail, password_attempt,log=None,close_cnx=True):
    query    = "SELECT id, password FROM users WHERE mail = %s;"
    values   = (mail,)
    results  = db.get_query_results(query,values,unique=False,close_cnx=False)

    for user in results:
        user_id         = user['id']
        hash_saved      = user['password']
        valid           = secure_lib.compare_passwords(password_attempt,hash_saved)

        if valid:
            return get_user_data_by_id(db, user_id,close_cnx=close_cnx)
    return None

def get_user_data_FromLogin(db,login, password,log=None,close_cnx=True):
    user_mail       = get_user_data_by_mailPassword(db,login, password,log=log,close_cnx=False)
    user_username   = get_user_data_by_usernamePassword(db,login, password,log=log,close_cnx=close_cnx)
    if user_mail is not None:
        return user_mail
    if user_username is not None:
        return user_username
    return None

def get_user_data(db, value, column, close_cnx=True,log=None):
    ''' Get the user role associated with given column'''
    query    = "SELECT * FROM users WHERE -lookup- = %s;"
    query    = query.replace("-lookup-", column)
 
    values   = (value,)

    results  = db.get_query_results(query,values,unique=False,close_cnx=close_cnx)

    if len(results) != 0:
        return results[0]
    return {}

def get_user_data_by_id(db, user_id, close_cnx=True,log=None):
    return get_user_data(db, user_id, "id", close_cnx=close_cnx)
   
def get_user_data_by_logged_token(db, token, close_cnx=True,log=None):
    return get_user_data(db, token, "token", close_cnx=close_cnx)
    
def get_user_data_by_registration_token(db, token, close_cnx=True,log=None):
    return get_user_data(db, token, "registration_token", close_cnx=close_cnx)
    
def get_user_data_by_password_reset_token(db, token, close_cnx=True,log=None):
    return get_user_data(db, token, "password_reset_token", close_cnx=close_cnx)
        
def get_user_data_by_mail(db, mail, close_cnx=True,log=None):
    return get_user_data(db, mail, "mail", close_cnx=close_cnx)
    
def get_user_data_by_username(db, username, close_cnx=True,log=None):
    return get_user_data(db, username, "username", close_cnx=close_cnx)
      
def get_user_data_by_telegram_id(db, telegram_id, close_cnx=True,log=None):
    return get_user_data(db, telegram_id, "telegram_id", close_cnx=close_cnx)

def update_users(db,close_cnx=True):
    ''' Update all golliath users '''
    # Connect to db
    
    # Set expired states if needed
    query = "UPDATE users SET role = 0 WHERE expire <= UTC_TIMESTAMP();"
    db.execute_query(query,None,close_cnx=False)
    
    # Set expired states if needed
    query = "UPDATE users SET password_reset_token = 'consumed' WHERE password_reset_token_expire <= UTC_TIMESTAMP();"
    db.execute_query(query,None,close_cnx=False)
    
    # Remove non activated in time accounts
    query = "DELETE FROM users WHERE role = -1 AND date_registred + INTERVAL 15 MINUTE > UTC_TIMESTAMP();"
    db.execute_query(query,None,close_cnx=False)
    
    # Remove expired sessions
    query = "DELETE FROM users_sessions WHERE expire <= UTC_TIMESTAMP();"
    db.execute_query(query,None,close_cnx=close_cnx)
                 
def is_valid_mail(db,email,close_cnx=True): #TODO: update
    query    = "SELECT email FROM mailing_list where email = %s;"
    values   = (email,)
    results  = db.get_query_results(query,values,close_cnx=close_cnx)
    valid    = len([x['email'] for x in results]) != 0
    return valid

def get_all_address_mails(db,close_cnx=True):
    query       = "SELECT distinct email FROM mailing_list;"
    results     = db.get_query_results(query,None,close_cnx=close_cnx) 
    emails      = [x['email'] for x in results]
    return emails