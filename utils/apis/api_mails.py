from ...libs import user_lib, sql_lib, secure_lib, mail_lib

def stay_in_touch(api,user_mail,name,token,cnx,close_cnx=True):
    status        = None
    valid_token   = mail_lib.is_mail_token_valid(user_mail, token)
    if not valid_token:
        api.set_error('invalid_token')

    status                  = user_lib.is_valid_mail(cnx,user_mail,close_cnx=True)
    if not status:
        return api.set_error('invalid_mail')

    parameters          = {'mail':user_mail,'name':name}
    mail_config         = api.get_config(['mails','stay_in_touch'])

    api.send_mail(
        mail_config     = mail_config,
        parameters_list = [parameters],
        cnx=cnx,log=api.log,close_cnx=close_cnx
    )

def mail_me(api,cnx,close_cnx=True):
    parameters          = {'mail':"durand.aurele@gmail.com",'name':'Aurele'}
    mail_config         = api.get_config(['mails','mail'])

    api.send_mail(
        mail_config     = mail_config,
        parameters_list = [parameters],
        cnx=cnx,log=api.log,close_cnx=close_cnx
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
    parameters = {}
    parameters_str = parameters_str[1:][::-1][1:][::-1]
    splt = parameters_str.split(',')
    for tupleStr in splt:
        key, value = tupleStr.split(':')
        parameters[unstring_value(key)] = unstring_value(value)
    return parameters

def request_view(api,user_mail,token,mail_type,mail_id,cnx,close_cnx=True):
    parameters  = None
    mail_token  = mail_lib.get_mail_token(user_mail)
    valid       = mail_token == token

    if not valid:
        return api.set_error('invalid_token')
    
    query       = "SELECT * from mails_history where mail_type = %s and uuid = %s"
    values      = (mail_type,mail_id)
    results     = sql_lib.get_query_results(cnx,query,values,unique=False,close_cnx=close_cnx)
    valid       = len(results) != 0
    if not valid:
        return api.set_error('no_mail')
        
    parameters = str_parameters_to_dict(results[0]['parameters_full'])
    parameters = [{'key':x,'value':y} for x,y in parameters.items()]
    api.set_data(parameters)

def request_unsubscribe(api,user_mail, token, mail_type,cnx,close_cnx=True):
    mail_token  = mail_lib.get_mail_token(user_mail)
    valid       = mail_token == token

    if not valid:
        return api.set_error('invalid_token')

    query   = "INSERT INTO mails_blacklist (mail,mail_type) VALUES (%s,%s)"
    values  = (user_mail,mail_type)
    valid   = sql_lib.execute_query(cnx, query,values,close_cnx=close_cnx)

    if not valid:
        return api.set_error('fail')