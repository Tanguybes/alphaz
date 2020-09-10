import json
from ...libs import user_lib, sql_lib, secure_lib, mail_lib

def stay_in_touch(api,user_mail,name,token,db,close_cnx=True):
    status        = None
    valid_token   = mail_lib.is_mail_token_valid(user_mail, token)
    if not valid_token:
        api.set_error('invalid_token')

    status                  = user_lib.is_valid_mail(db,user_mail,close_cnx=True)
    if not status:
        return api.set_error('invalid_mail')

    parameters          = {'mail':user_mail,'name':name}

    api.send_mail(
        mail_config     = 'stay_in_touch',
        parameters_list = [parameters],
        db=db,log=api.log,close_cnx=close_cnx
    )

def mail_me(api,db,close_cnx=True):
    parameters          = {'mail':"durand.aurele@gmail.com",'name':'Aurele'}

    api.send_mail(
        mail_config     = 'mail',
        parameters_list = [parameters],
        db=db,close_cnx=close_cnx
    )

def unstring_value(value):
    value = value.strip()
    if value[0] == "'" or value[0] == '"':
        value = value[1:]
    if value[-1] == "'" or value[-1] == '"':
        value = value[::-1][1:][::-1]
    value = value.strip()
    return value

def str_parameters_to_dict(parameters_str):
    parameters = json.loads(parameters_str)
    return parameters

def request_view(api,user_mail,token,mail_type,mail_id,db,close_cnx=True):
    mail_type   = mail_lib.get_mail_type(mail_type)
    parameters  = None
    mail_token  = mail_lib.get_mail_token(user_mail)
    valid       = mail_token == token

    if not valid:
        return api.set_error('invalid_token')
    
    query       = "SELECT * from mails_history where mail_type = %s and uuid = %s"
    values      = (mail_type,mail_id)
    results     = db.get_query_results(query,values,unique=False,close_cnx=close_cnx)
    valid       = len(results) != 0
    if not valid:
        return api.set_error('no_mail')
        
    parameters = str_parameters_to_dict(results[0]['parameters_full'])
    parameters['mail'] = user_mail
    #parameters = [{'key':x,'value':y} for x,y in parameters.items()]

    mail_path = api.get_config('mails/path')
    mail_contents_list = mail_lib.get_mail_content_for_parameters(mail_path,mail_type,[parameters],api.log)

    if len(mail_contents_list) == 0:
        api.set_error('mail_error')
    else:
        api.set_data(mail_contents_list[0]['content'])

def request_unsubscribe(api,user_mail, token, mail_type,db,close_cnx=True):
    mail_type   = mail_lib.get_mail_type(mail_type)
    mail_token  = mail_lib.get_mail_token(user_mail)
    valid       = mail_token == token

    if not valid:
        return api.set_error('invalid_token')

    query   = "INSERT INTO mail_blacklist (mail,mail_type) VALUES (%s,%s)"
    values  = (user_mail,mail_type)
    valid   = db.execute_query(query,values,close_cnx=close_cnx)

    if not valid:
        return api.set_error('fail')