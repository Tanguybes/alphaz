import datetime, jwt
from ..libs import user_lib, sql_lib, secure_lib

from ..models.database import main_definitions as defs

from ..models.main import AlphaException

from core import core

DB = core.get_database("users")

# Serve for registration
def try_register_user(api,mail, username, password, password_confirmation):
    userByMail          = user_lib.get_user_data_by_mail(DB,mail)
    userByUsername      = user_lib.get_user_data_by_username(DB,username)

    if 'id' in userByMail or 'id' in userByUsername:
        if ('id' in userByMail and userByMail['role'] < 0) or ('id' in userByUsername and userByUsername['role'] < 0):
            raise AlphaException('account_not_validated')
        raise AlphaException('account_duplicated')
    
    if password != password_confirmation:
        raise AlphaException('password_missmatch')
    
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
        db              = DB
    )

    if sent:
        DB.add(defs.User(username=username,mail=mail,password=password_hashed,role=-1,
            date_registred=datetime.datetime.now(),last_activity=datetime.datetime.now(),
            registration_token=token))
    else:
        AlphaException('sending')

def ask_password_reset(api,username_or_mail):
    user_by_mail        = user_lib.get_user_data_by_mail(DB,username_or_mail)
    user_by_username    = user_lib.get_user_data_by_username(DB,username_or_mail)

    if len(user_by_mail.keys()) == 0 and len(user_by_username.keys()) == 0:
        raise AlphaException('unknown_inputs')
     
    if 'id' not in user_by_mail and 'id' not in user_by_username:
        raise AlphaException('unknown_inputs')   

    user_data   = user_by_mail if 'id' in user_by_mail else user_by_username

    # Generate token
    token       = secure_lib.get_token()

    query       = "UPDATE user SET password_reset_token = %s, password_reset_token_expire = UTC_TIMESTAMP() + INTERVAL 20 MINUTE WHERE id = %s;"
    values      = (token, user_data['id'],)

    if not DB.execute_query(query,values,log=None):
        raise AlphaException('sql_error')    

    # MAIL
    parameters              = {}
    parameters["mail"]      = user_data['mail']
    parameters["token"]     = token
    parameters["username"]  = user_data['username']
    parameters["name"]      = user_data['username']

    mail_sent = api.send_mail(
        mail_config     = 'password_reset',
        parameters_list = [parameters],
        db=DB
    )  

def confirm_user_registration(api,token):
    if 'consumed' in token:
        raise AlphaException('invalid_token') 
    user_data = user_lib.get_user_data_by_registration_token(DB,token)

    if len(user_data) == 0:
        AlphaException('not_found')

    if 'id' in user_data:
        # Set Role to 0 and revoke token
        user = DB.select(defs.User,filters={
            'id': user_data['id']
        },first=True,json=False)
        if user is None:
            raise AlphaException('error')
        user.role = 0
        user.registration_token = 'consumed'
        DB.commit()
        
        valid = True
        if not valid:
            raise AlphaException('error')   

# Serve for web logins
def try_login(api,login, password, ip):
    user_data = user_lib.get_user_data_FromLogin(DB,login, password)
    if user_data is not None:
        if user_data['role'] >= 0:
            # Generate token
            encoded_jwt = jwt.encode({
                'username': user_data['username'], 
                'id': user_data['id'], 
                'time': str(datetime.datetime.now())}, api.config['JWT_SECRET_kEY'], algorithm='HS256').decode('ascii')
            #todo: make sure JWT_SECRET_kEY exist

            # Add new token session related to user
            DB.add(defs.UserSession(
                user_id=user_data['id'],
                token=encoded_jwt,
                ip=ip,
                expire=datetime.datetime.now() + datetime.timedelta(days=7)
            ))
            valid = True #TODO: edit
            if valid:
                data = {
                    'user':{x:y for x,y in user_data.items()},
                    'token': encoded_jwt,
                    'valid_until': datetime.datetime.now() + datetime.timedelta(days=7)
                }
                return data
            raise AlphaException('error')
        else:
            raise AlphaException('account_not_validated')
    raise AlphaException('unknown_user') 

def confirm_user_password_reset(api,token, password, password_confirmation):
    if 'consumed' in token:
        raise AlphaException('consumed_token') 

    user_data = user_lib.get_user_data_by_password_reset_token(DB,token)
    if not 'id' in user_data:
        raise AlphaException('invalid_token') 
    
    try_reset_password(api,user_data, password, password_confirmation)

def try_reset_password(api,user_data, password, password_confirmation,log=None):
    if password != password_confirmation:
        raise AlphaException('password_missmatch') 

    '''if not password_check_format(password):
        return "password_format"'''
    # Set New password and revoke token
    password_hashed = secure_lib.secure_password(password)
   
    # Reset password
    query   = "UPDATE user SET password = %s, password_reset_token = 'consumed' WHERE id = %s;"
    values  = (password_hashed, user_data['id'],)
    valid   = DB.execute_query(query,values)
    if not valid:
        AlphaException('reset_error') 
    
    # Reset all sessions as password changed
    query   = "DELETE FROM user_session WHERE user_id = %s;"
    values  = (user_data['id'],)
    valid   = DB.execute_query(query,values)
    if not valid:
        AlphaException('clean_error')

def logout(api,token,log=None):
    valid = DB.delete(defs.UserSession,filters={'token': token})

    """
    user_session = DB.select(defs.UserSession,filters={
        'token': token
    },first=True,json=False)

    if user_session is not None:
        DB.delete(user_session)
    valid = True #todo: upgrade
    """
    if not valid:
        AlphaException('fail')

def get_user_dataFromToken(token):
    user_id     = None
    results     = DB.select(defs.UserSession,filters=[defs.UserSession.token==token],json=True)
    if len(results) != 0:
        user_id = results[0]['user_id']

    if user_id is not None:
        return user_lib.get_user_data_by_id(DB, user_id)
    return None

def try_subscribe_user(api,mail, nb_days, target_role):
    userByMail          = user_lib.get_user_data_by_mail(DB,mail)
    user_data = None
    if 'id' in userByMail:
        if 'id' in userByMail:
            user_data = userByMail
    expired_date = datetime.datetime.now() + datetime.timedelta(days=nb_days)
    if user_data is not None:
        # Reset password
        query  = "UPDATE user SET role = %s, expire = %s WHERE id = %s;"
        values = (target_role, expired_date, user_data['id'],)
        valid  = DB.execute_query(query,values)
        if not valid:
            AlphaException('update_error')
    AlphaException('unknow_user')