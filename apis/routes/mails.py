from ...utils.api import route, Parameter

from core import core

api         = core.api
db          = core.db
log         = core.get_logger('api')

category    = "mails"

@route('/mails/mailme',category=category,logged=False,cache=False)
def mail_me():
    api_mails.mail_me(api,db,close_cnx=True)

@route('/mails/stayintouch',category=category,logged=False,cache=False, 
    parameters = [
        Parameter('token',required=True),
        Parameter('mail',required=True),
        Parameter('name',required=True)
    ])
def mails_stay_in_touch():
    token           = api.get('token')
    user_mail       = api.get('mail')
    name            = api.get('name')

    api_mails.stay_in_touch(api,user_mail,name, token,db)

@route('/mails/newsletter',category=category,
    parameters = [
        Parameter('mail',required=True),
        Parameter('name',required=True)
    ]
)
def mail_newsletter():
    db.insert(defs.NewsLetter,values=api.dataGet)
    api.set_data('saved') 

@route('/mails/requestview',category=category,logged=False,cache=False, 
    parameters = [
        Parameter('token',required=True),
        Parameter('mail',required=True),
        Parameter('name',required=True),
        Parameter('id',required=True)
    ])
def mails_request_view():
    token       = api.get('token')
    user_mail   = api.get('mail')
    mail_type   = api.get('name')
    mail_id     = api.get('id')

    api_mails.request_view(api,user_mail,token,mail_type,mail_id,db,close_cnx=True)

@route('/mails/unsubscribe',category=category,logged=False,cache=False, 
    parameters = [
        Parameter('token',required=True),
        Parameter('mail',required=True),
        Parameter('type',required=True)
    ])
def mails_unsubscribe():
    token       = api.get('token')
    user_mail   = api.get('mail')
    mail_type   = api.get('type')

    api_mails.request_unsubscribe(api,user_mail,token,mail_type,db,close_cnx=True)