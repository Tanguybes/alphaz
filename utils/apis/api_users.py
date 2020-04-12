import datetime, jwt
from ...libs import user_lib, sql_lib, secure_lib

# Serve for registration
def try_register_user(api,cnx,mail, username, password, password_confirmation,close_cnx=True):
    userByMail          = user_lib.get_user_dataByMail(cnx,mail,close_cnx=False)
    userByUsername      = user_lib.get_user_dataByUsername(cnx,username,close_cnx=False)

    if 'id' in userByMail or 'id' in userByUsername:
        if ('id' in userByMail and userByMail['role'] < 0) or userByUsername['role'] < 0:
            return api.set_error('account_not_validated')
        return api.set_error('account_duplicated')
    
    if password != password_confirmation:
        return api.set_error('password_missmatch')
    
    '''mail_valid = validate_email(mail)
    if not mail_valid:
        return "mail_format"'''
    
    '''if not password_check_format(password):
        return "password_format"'''
    
    password_hashed = secure_lib.secure_password(password)
    
    # ADD CHECKS FOR LENGHT OF USERNAME/MAIL!!
    
    # Generate token
    token   = secure_lib.get_token()

    parameters = {
        "token": token,
        "name": username,
        "mail": mail
    }

    api.send_mail(
        mail_config     = 'registration',
        parameters_list = [parameters],
        cnx             = cnx,
        close_cnx       = close_cnx
    )

    query   = "INSERT INTO users (username, mail, password, role, date_registred, last_activity, registration_token) VALUES (%s, %s, %s, -1, UTC_TIMESTAMP(), UTC_TIMESTAMP(), %s)"
    values  = (username, mail, password_hashed, token,)
    cnx.execute_query(query,values,close_cnx=close_cnx)

    #sender      = CoreW.CONSTANTS['email-registration']

def ask_password_reset(api,username_or_mail,cnx,close_cnx=True):
    user_by_mail        = user_lib.get_user_dataByMail(cnx,username_or_mail,close_cnx=False)
    user_by_username    = user_lib.get_user_dataByUsername(cnx,username_or_mail,close_cnx=False,log=api.log)

    if len(user_by_mail.keys()) == 0 and len(user_by_username.keys()) == 0:
        return api.set_error('unknown_inputs')
     
    if 'id' not in user_by_mail and 'id' not in user_by_username:
        return api.set_error('unknown_inputs')   

    user_data = user_by_mail if 'id' in user_by_mail else user_by_username

    # Generate token
    token   = secure_lib.get_token()

    query   = "UPDATE users SET password_reset_token = %s, password_reset_token_expire = UTC_TIMESTAMP() + INTERVAL 20 MINUTE WHERE id = %s;"
    values  = (token, user_data['id'],)

    if not cnx.execute_query(query,values,close_cnx=False,log=None):
        return api.set_error('sql_error')    

    # MAIL
    mail_config             = api.get_config(['mails','password_reset'])

    parameters              = {}
    parameters["mail"]      = user_data['mail']
    parameters["token"]     = token
    parameters["username"]  = user_data['username']
    parameters["name"]      = user_data['username']

    api.send_mail(
        mail_config     = mail_config,
        parameters_list = [parameters],
        cnx=cnx,log=api.log,close_cnx=close_cnx
    )  

def confirm_user_registration(api,token,cnx):
    if 'consumed' in token:
        return api.set_error('invalid_token') 
    user_data = user_lib.get_user_dataByRegistrationToken(cnx,token,close_cnx=False)
    if 'id' in user_data:
        # Set Role to 0 and revoke token
        query   = "UPDATE users SET role = 0, registration_token = 'consumed' WHERE id = %s"
        values  = (user_data['id'],)
        valid   = cnx.execute_query(query,values,close_cnx=True,log=api.log)
        if not valid:
            return api.set_error('error')   

# Serve for web logins
def try_login(api,cnx,login, password, ip):
    user_data = user_lib.get_user_data_FromLogin(cnx,login, password,close_cnx=False,log=api.log)
    if user_data is not None:
        if user_data['role'] >= 0:
            # Generate token
            encoded_jwt = jwt.encode({
                'username': user_data['username'], 
                'id': user_data['id'], 
                'time': str(datetime.datetime.now())}, api.get_config('jwt_key'), algorithm='HS256')

            # Add new token session related to user
            query   = "INSERT INTO users_sessions (user_id, token, ip, expire) VALUES (%s, %s, %s, UTC_TIMESTAMP() + INTERVAL 7 DAY)"
            values  = (user_data['id'], encoded_jwt, ip,)
            valid   = cnx.execute_query(query,values,close_cnx=True,log=api.log)
            if valid:
                data = {
                    'user':user_data,
                    'token': encoded_jwt,
                    'valid_until': datetime.datetime.now() + datetime.timedelta(days=7)
                }
                return api.set_data(data)
            return api.set_error('error')
        else:
            return api.set_error('account_not_validated')
    return api.set_error('unknown_user') 

def confirm_user_password_reset(api,token, password, password_confirmation,cnx):
    if 'consumed' in token:
        return api.set_error('consumed_token') 

    user_data = user_lib.get_user_dataByPasswordResetToken(cnx,token, close_cnx=False,log=api.log)
    if not 'id' in user_data:
        return api.set_error('invalid_token') 
    
    try_reset_password(api,user_data, password, password_confirmation,cnx=cnx,log=api.log,close_cnx=True)

def try_reset_password(api,user_data, password, password_confirmation,cnx,log=None,close_cnx=True):
    if password != password_confirmation:
        return api.set_error('password_missmatch') 

    '''if not password_check_format(password):
        return "password_format"'''
    # Set New password and revoke token
    password_hashed = secure_lib.secure_password(password)
   
    # Reset password
    query   = "UPDATE users SET password = %s, password_reset_token = 'consumed' WHERE id = %s;"
    values  = (password_hashed, user_data['id'],)
    valid   = cnx.execute_query(query,values,close_cnx=False,log=api.log)
    if not valid:
        api.set_error('reset_error') 
    
    # Reset all sessions as password changed
    query   = "DELETE FROM users_sessions WHERE user_id = %s;"
    values  = (user_data['id'],)
    valid   = cnx.execute_query(query,values,close_cnx=close_cnx,log=api.log)
    if not valid:
        api.set_error('clean_error')

def logout(api,token,cnx,log=None,close_cnx=True):
    query = "DELETE FROM users_sessions WHERE token = %s;"
    values = (token,)
    valid   = cnx.execute_query(query,values,close_cnx=close_cnx,log=api.log)
    if not valid:
        api.set_error('fail')

def get_user_dataFromToken(api,cnx,token):
    user_id     = None
    query       = ("SELECT user_id FROM users_sessions WHERE token = %s")
    values      = (token,)
    results     = cnx.get_query_results(query,values,unique=True,close_cnx=False)
    if len(results) != 0:
        user_id = results[0]

    if user_id is not None:
        return user_lib.get_user_dataById(cnx, user_id)
    return None

def try_subscribe_user(api,mail, nb_days, target_role,cnx,close_cnx=True):
    userByMail          = user_lib.get_user_dataByMail(cnx,mail,close_cnx=False)
    user_data = None
    if 'id' in userByMail:
        if 'id' in userByMail:
            user_data = userByMail
    expired_date = datetime.datetime.now() + datetime.timedelta(days=nb_days)
    if user_data is not None:
        # Reset password
        query  = "UPDATE users SET role = %s, expire = %s WHERE id = %s;"
        values = (target_role, expired_date, user_data['id'],)
        valid  = cnx.execute_query(query,values,close_cnx=close_cnx)
        if not valid:
            api.set_error('update_error')
    api.set_error('unknow_user')