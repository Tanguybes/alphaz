from . import sql_lib, secure_lib

def get_user_dataByUsernamePassword(cnx,username, password_attempt,log=None,close_cnx=True):
    query    = "SELECT id, password FROM users WHERE username = %s;"
    values   = (username,)

    results  = cnx.get_query_results(query,values,unique=False,close_cnx=False)

    for user in results:
        user_id         = user['id']
        hash_saved      = user['password']
        valid           = secure_lib.compare_passwords(password_attempt,hash_saved)
        if valid:
            return get_user_dataById(cnx, user_id,close_cnx=close_cnx)
    return None

def get_user_dataByMailPassword(cnx,mail, password_attempt,log=None,close_cnx=True):
    query    = "SELECT id, password FROM users WHERE mail = %s;"
    values   = (mail,)
    results  = cnx.get_query_results(query,values,unique=False,close_cnx=False)

    for user in results:
        user_id         = user['id']
        hash_saved      = user['password']
        valid           = secure_lib.compare_passwords(password_attempt,hash_saved)

        if valid:
            return get_user_dataById(cnx, user_id,close_cnx=close_cnx)
    return None

def get_user_data_FromLogin(cnx,login, password,log=None,close_cnx=True):
    user_mail       = get_user_dataByMailPassword(cnx,login, password,log=log,close_cnx=False)
    user_username   = get_user_dataByUsernamePassword(cnx,login, password,log=log,close_cnx=close_cnx)
    if user_mail is not None:
        return user_mail
    if user_username is not None:
        return user_username
    return None

def get_user_data(cnx, value, column, close_cnx=True,log=None):
    ''' Get the user role associated with given column'''
    query    = "SELECT * FROM users WHERE -lookup- = %s;"
    query    = query.replace("-lookup-", column)
 
    values   = (value,)

    results  = cnx.get_query_results(query,values,unique=False,close_cnx=close_cnx)

    if len(results) != 0:
        return results[0]
    return {}

def get_user_dataById(cnx, user_id, close_cnx=True,log=None):
    return get_user_data(cnx, user_id, "id", close_cnx=close_cnx)
   
def get_user_dataByLoggedToken(cnx, token, close_cnx=True,log=None):
    return get_user_data(cnx, token, "token", close_cnx=close_cnx)
    
def get_user_dataByRegistrationToken(cnx, token, close_cnx=True,log=None):
    return get_user_data(cnx, token, "registration_token", close_cnx=close_cnx)
    
def get_user_dataByPasswordResetToken(cnx, token, close_cnx=True,log=None):
    return get_user_data(cnx, token, "password_reset_token", close_cnx=close_cnx)
        
def get_user_dataByMail(cnx, mail, close_cnx=True,log=None):
    return get_user_data(cnx, mail, "mail", close_cnx=close_cnx)
    
def get_user_dataByUsername(cnx, username, close_cnx=True,log=None):
    return get_user_data(cnx, username, "username", close_cnx=close_cnx)
      
def get_user_dataByTelegramId(cnx, telegram_id, close_cnx=True,log=None):
    return get_user_data(cnx, telegram_id, "telegram_id", close_cnx=close_cnx)

def update_users(cnx,close_cnx=True):
    ''' Update all golliath users '''
    # Connect to db
    
    # Set expired states if needed
    query = "UPDATE users SET role = 0 WHERE expire <= UTC_TIMESTAMP();"
    cnx.execute_query(query,None,close_cnx=False)
    
    # Set expired states if needed
    query = "UPDATE users SET password_reset_token = 'consumed' WHERE password_reset_token_expire <= UTC_TIMESTAMP();"
    cnx.execute_query(query,None,close_cnx=False)
    
    # Remove non activated in time accounts
    query = "DELETE FROM users WHERE role = -1 AND date_registred + INTERVAL 15 MINUTE > UTC_TIMESTAMP();"
    cnx.execute_query(query,None,close_cnx=False)
    
    # Remove expired sessions
    query = "DELETE FROM users_sessions WHERE expire <= UTC_TIMESTAMP();"
    cnx.execute_query(query,None,close_cnx=close_cnx)
                 
def is_valid_mail(cnx,email,close_cnx=True): #TODO: update
    query    = "SELECT email FROM mailing_list where email = %s;"
    values   = (email,)
    results  = cnx.get_query_results(query,values,close_cnx=close_cnx)
    valid    = len([x['email'] for x in results]) != 0
    return valid

def get_all_address_mails(cnx,close_cnx=True):
    query       = "SELECT distinct email FROM mailing_list;"
    results     = cnx.get_query_results(query,None,close_cnx=close_cnx) 
    emails      = [x['email'] for x in results]
    return emails