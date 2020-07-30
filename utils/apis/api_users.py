import datetime, jwt
from ...libs import user_lib, sql_lib, secure_lib

from ...models.database import definitions as defs

# Serve for registration
def try_register_user(api,db,mail, username, password, password_confirmation,close_cnx=True):
    userByMail          = user_lib.get_user_data_by_mail(db,mail,close_cnx=False)
    userByUsername      = user_lib.get_user_data_by_username(db,username,close_cnx=False)

    if 'id' in userByMail or 'id' in userByUsername:
        if ('id' in userByMail and userByMail['role'] < 0) or ('id' in userByUsername and userByUsername['role'] < 0):
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

    sent = api.send_mail(
        mail_config     = 'registration',
        parameters_list = [parameters],
        db              = db,
        close_cnx       = close_cnx
    )

    if sent:
        db.add(defs.User(username=username,mail=mail,password=password_hashed,role=-1,
            date_registred=datetime.datetime.utcnow(),last_activity=datetime.datetime.utcnow(),
            registration_token=token))
    else:
        api.set_error('sending')
    #sender      = CoreW.CONSTANTS['email-registration']

def ask_password_reset(api,username_or_mail,db,close_cnx=True):
    user_by_mail        = user_lib.get_user_data_by_mail(db,username_or_mail,close_cnx=False)
    user_by_username    = user_lib.get_user_data_by_username(db,username_or_mail,close_cnx=False)

    if len(user_by_mail.keys()) == 0 and len(user_by_username.keys()) == 0:
        return api.set_error('unknown_inputs')
     
    if 'id' not in user_by_mail and 'id' not in user_by_username:
        return api.set_error('unknown_inputs')   

    user_data   = user_by_mail if 'id' in user_by_mail else user_by_username

    # Generate token
    token       = secure_lib.get_token()

    query       = "UPDATE user SET password_reset_token = %s, password_reset_token_expire = UTC_TIMESTAMP() + INTERVAL 20 MINUTE WHERE id = %s;"
    values      = (token, user_data['id'],)

    if not db.execute_query(query,values,close_cnx=False,log=None):
        return api.set_error('sql_error')    

    # MAIL
    parameters              = {}
    parameters["mail"]      = user_data['mail']
    parameters["token"]     = token
    parameters["username"]  = user_data['username']
    parameters["name"]      = user_data['username']

    mail_sent = api.send_mail(
        mail_config     = 'password_reset',
        parameters_list = [parameters],
        db=db,close_cnx=close_cnx
    )  

def confirm_user_registration(api,token,db):
    if 'consumed' in token:
        return api.set_error('invalid_token') 
    user_data = user_lib.get_user_data_by_registration_token(db,token,close_cnx=False)

    if len(user_data) == 0:
        api.set_error('not_found')

    if 'id' in user_data:
        # Set Role to 0 and revoke token
        user = db.select(defs.User,filters={
            'id': user_data['id']
        },first=True,json=False)
        #            'role':0,
        #    'registration_token':'consumed'
        if user is None:
            return api.set_error('error')
        user.role = 0
        user.registration_token = 'consumed'
        db.commit()
        
        valid = True
        #query   = "UPDATE user SET role = 0, registration_token = 'consumed' WHERE id = %s"
        #values  = (user_data['id'],)
        #valid   = db.execute_query(query,values,close_cnx=True)
        if not valid:
            return api.set_error('error')   

# Serve for web logins
def try_login(api,db,login, password, ip):
    user_data = user_lib.get_user_data_FromLogin(db,login, password,close_cnx=False)
    if user_data is not None:
        if user_data['role'] >= 0:
            # Generate token
            encoded_jwt = jwt.encode({
                'username': user_data['username'], 
                'id': user_data['id'], 
                'time': str(datetime.datetime.now())}, api.config['JWT_SECRET_kEY'], algorithm='HS256').decode('ascii')
            #todo: make sure JWT_SECRET_kEY exist

            # Add new token session related to user
            db.add(defs.UserSession(
                user_id=user_data['id'],
                token=encoded_jwt,
                ip=ip,
                expire=datetime.datetime.utcnow() + datetime.timedelta(days=7)
            ))
            valid = True #TODO: edit
            if valid:
                data = {
                    'user':{x:y for x,y in user_data.items()},
                    'token': encoded_jwt,
                    'valid_until': datetime.datetime.now() + datetime.timedelta(days=7)
                }
                return api.set_data(data)
            return api.set_error('error')
        else:
            return api.set_error('account_not_validated')
    return api.set_error('unknown_user') 

def confirm_user_password_reset(api,token, password, password_confirmation,db):
    if 'consumed' in token:
        return api.set_error('consumed_token') 

    user_data = user_lib.get_user_data_by_password_reset_token(db,token, close_cnx=False)
    if not 'id' in user_data:
        return api.set_error('invalid_token') 
    
    try_reset_password(api,user_data, password, password_confirmation,db=db,close_cnx=True)

def try_reset_password(api,user_data, password, password_confirmation,db,log=None,close_cnx=True):
    if password != password_confirmation:
        return api.set_error('password_missmatch') 

    '''if not password_check_format(password):
        return "password_format"'''
    # Set New password and revoke token
    password_hashed = secure_lib.secure_password(password)

    print('RESET ',password,password_hashed)
   
    # Reset password
    query   = "UPDATE user SET password = %s, password_reset_token = 'consumed' WHERE id = %s;"
    values  = (password_hashed, user_data['id'],)
    valid   = db.execute_query(query,values,close_cnx=False)
    if not valid:
        api.set_error('reset_error') 
    
    # Reset all sessions as password changed
    query   = "DELETE FROM user_session WHERE user_id = %s;"
    values  = (user_data['id'],)
    valid   = db.execute_query(query,values,close_cnx=close_cnx)
    if not valid:
        api.set_error('clean_error')

def logout(api,token,db,log=None,close_cnx=True):
    valid = db.delete(defs.UserSession,filters={'token': token})

    """
    user_session = db.select(defs.UserSession,filters={
        'token': token
    },first=True,json=False)

    if user_session is not None:
        db.delete(user_session)
    valid = True #todo: upgrade
    """
    if not valid:
        api.set_error('fail')

def get_user_dataFromToken(api,db,token):
    user_id     = None
    query       = ("SELECT user_id FROM user_session WHERE token = %s")
    values      = (token,)
    results     = db.get_query_results(query,values,unique=True,close_cnx=False)

    if len(results) != 0:
        user_id = results[0]

    if user_id is not None:
        return user_lib.get_user_data_by_id(db, user_id)
    return None

def try_subscribe_user(api,mail, nb_days, target_role,db,close_cnx=True):
    userByMail          = user_lib.get_user_data_by_mail(db,mail,close_cnx=False)
    user_data = None
    if 'id' in userByMail:
        if 'id' in userByMail:
            user_data = userByMail
    expired_date = datetime.datetime.now() + datetime.timedelta(days=nb_days)
    if user_data is not None:
        # Reset password
        query  = "UPDATE user SET role = %s, expire = %s WHERE id = %s;"
        values = (target_role, expired_date, user_data['id'],)
        valid  = db.execute_query(query,values,close_cnx=close_cnx)
        if not valid:
            api.set_error('update_error')
    api.set_error('unknow_user')