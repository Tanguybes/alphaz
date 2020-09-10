from ...utils.api import route, Parameter

from core import core

api         = core.api
db          = core.db
log         = core.get_logger('api')

category    = 'user'

@route('/register',category=category, methods = ['POST'],
    parameters = [
        Parameter('mail',required=True),
        Parameter('username',required=True),
        Parameter('password',required=True),
        Parameter('password_confirmation',required=True),
    ])
def register():
    if api.get_logged_user() is not None:
        return api.set_error('logged')

    api_users.try_register_user(
        api,
        db,
        api.get('mail'), 
        api.get('username'), 
        api.get('password'), 
        api.get('password_confirmation'))

@route('/register/validation',category=category,methods = ['GET'],
    parameters  = [
        Parameter('tmp_token',required=True)
    ],
    parameters_names=[])
def register_validation():
    if api.get_logged_user() is not None:
        return api.set_error('logged')

    api_users.confirm_user_registration(api,token   = api.get('tmp_token'),db=db)

# LOGIN
@route('/auth',category=category, methods = ['POST'],
    parameters  = [
        Parameter('username',required=True),
        Parameter('password',required=True)
    ])
def login():
    api_users.try_login(api, db, api.get('username'), api.get('password'), request.remote_addr)

@route('/password/lost',category=category, methods = ['POST'],
    parameters = [
        Parameter('username',required=False),
        Parameter('mail',required=False)
    ])
def password_lost():
    if api.get_logged_user() is not None:
        return api.set_error('logged')

    username    = api.get('username')
    mail        = api.get('mail')

    if username is not None or mail is not None:
        username_or_mail    = username if mail is None else mail
        api_users.ask_password_reset(api,username_or_mail,db=db) 
    else:
        api.set_error('inputs')

@route('/password/reset',category=category, methods = ['GET', 'POST'],
    parameters  = [
        Parameter('tmp_token',required=True),
        Parameter('password',required=True),
        Parameter('password_confirmation',required=True)
    ])
def password_reset_validation():
    if api.get_logged_user() is not None:
        return api.set_error('logged')

    api_users.confirm_user_password_reset(api,token=api.get('tmp_token'), password=api.get('password'), password_confirmation=api.get('password_confirmation'),db=db)

@route('/logout',category=category,cache=False,logged=False,methods = ['GET', 'POST'],
    parameters  = [],  parameters_names=[])
def logout():
    token   = api.get_token()

    api_users.logout(api,token,db=db)

@route('/profile/password',category=category, logged=True, methods = ['POST'],
    parameters  = [
        Parameter('password',required=True),
        Parameter('password_confirmation',required=True)
    ])
def reset_password():
    user_data               = api.get_logged_user()

    api_users.try_reset_password(api,user_data, api.get('password'), api.get('password_confirmation'),db=db,log=api.log)
    