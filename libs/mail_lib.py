import smtplib, socks, copy, json

import hashlib, re, os, datetime
from flask import current_app
from flask_mail import Message

import uuid
from . import sql_lib
from ..config.utils import merge_configuration, get_mails_parameters

MAIL_PARAMETERS_PATTERN = "[[%s]]"

def mail2(to_mails,subject,body,bodyHtml=None,attachments=[]):
    import win32com.client as win32
    outlook = win32.Dispatch('outlook.application')
    mail = outlook.CreateItem(0)
    mail.To = to_mails
    mail.Subject = subject
    mail.Body = body
    mail.HTMLBody = bodyHtml if bodyHtml is not None else body #this field is optional

    # To attach a file to the email (optional):
    if len(attachments) != 0:
    #attachment  = "Path to the attachment"
        for attachment in attachments:
            mail.Attachments.Add(attachment)

    mail.Send()

def mail(to_mails,from_mails,proxy_host, proxy_port):
    receivers = [to_mails]

    message = """From: From Person <from@fromdomain.com>
    To: To Person <to@todomain.com>
    Subject: SMTP e-mail test

    This is a test e-mail message.
    """
    
    if proxy_host is not None:
        socks.setdefaultproxy(socks.HTTP, proxy_host, proxy_port)
    socks.wrapmodule(smtplib)

    try:
       smtpObj = smtplib.SMTP('SMTP.office365.com')
       smtpObj.sendmail(from_mails, receivers, message)         
       print ("Successfully sent email")
    except Exception as ex:
       print ("Error: unable to send email: ",ex)
    
def get_mail_type(raw_mail_url):
    if 'mail-content=' in raw_mail_url:
        raw_mail_url = raw_mail_url.split('mail-content=')[1]
    if '&' in raw_mail_url:
        raw_mail_url = raw_mail_url.split('&')[0]
    return raw_mail_url

""" MAILS """
def get_mail_content(mail_root, mail_type,log):
    content = ""
    if not mail_root[-1] == os.sep:
        mail_root = mail_root + os.sep

    raw         = mail_type.split('?')[0]
    parameters  = {}
    if len(mail_type.split('?')) != 1:
        for el in mail_type.split('?')[1].split('&'):
            key, value = el.split('=')[0], el.split('=')[1]
            parameters[key] = value

    mail_path = mail_root + raw

    if os.path.exists(mail_path):
        with open(mail_path) as f:
            content  = f.read()

        for key, value in parameters.items():
            file_name  = mail_root + value + '.html'
            div_block  = r'<div id="%s">[^\<\>]*<\/div>'%key
            regex_find = re.findall(div_block,content)

            if len(regex_find) != 0:
                result = regex_find[0]
            else:
                log.error('Mail content is incorrect for %s, cannot div block by %s content (regex expression not matched: %s )'%(mail_path,file_name,div_block))
                return None

            with open(file_name) as f:
                div_content  = f.read()
            content = content.replace(result,div_content)
    else:
        log.error('Cannot find mail content at %s'%mail_path)
        return None

    script_starts = [m.start() for m in re.finditer('<script', content)]
    script_ends   = [m.start() for m in re.finditer('</script>', content)]

    script_blocks = []
    for i in range(len(script_starts)):
        script_blocks.append(content[script_starts[i]:script_ends[i] + len('</script>')])

    for script_block in script_blocks:
        content = content.replace(script_block,'')

    with open(mail_root + os.sep + 'generated_mail.html','w') as f:
        f.write(content)

    #return set_parameters(content,CoreW.CONSTANTS)
    return content

def get_mail_token(key):
    salt        = "%ThisIsGolliath38Pepper$"
    hash_string = key + salt
    hashed      = hashlib.sha256(hash_string.encode()).hexdigest()
    return hashed

def is_mail_token_valid(key,token):
    hashed = get_mail_token(key)
    return hashed == token

def get_title(content,default=''):
    title_regex = r'<title[^>]*>([^<]+)</title>'
    regex_find = re.findall(title_regex,content)

    if len(regex_find) != 0:
        result = regex_find[0]
    else:
        result = default if default is not None else ''
    return result

def set_parameters(content,parameters):
    for parameter, value in parameters.items():
        if value is not None:
            content = content.replace(MAIL_PARAMETERS_PATTERN%parameter,str(value))
    return content

def send_mail(title,host_web,mail_path,mail_type,parameters_list,sender,db,log,key_signature="<alpha mail>",close_cnx=True):
    print('Getting mail at %s/%s'%(mail_path,mail_type))
    content                 = get_mail_content(mail_path,mail_type,log)
    
    if content is None:
        return False
    parameters_to_specify   = get_mails_parameters(content)

    valid_signature         = key_signature in str(content) 
    #title               = get_title(content,default=default_tile)

    now     = datetime.datetime.now()
    year    = now.year
    month   = now.month
    hour    = now.hour
    minute  = now.minute
    second  = now.second

    for parameters in parameters_list:
        for key, value in parameters.items():
            if MAIL_PARAMETERS_PATTERN%key in title:
                title = title.replace(MAIL_PARAMETERS_PATTERN%key,value)

        uuidValue = str(uuid.uuid4())

        if not 'mail' in parameters.keys():
            log.error('Missing parameter <mail> for sending mail !')
            return False

        user_mail           = parameters['mail']
        token               = get_mail_token(user_mail)

        parameters['year']                  = year
        parameters['mail']                  = user_mail
        parameters['uuid']                  = uuidValue
        parameters['configuration']         = get_mail_type(mail_type)
        parameters['mail_token']            = token

        raw_parameters = copy.copy(parameters)
        for key, value in raw_parameters.items():
            for k, v in parameters.items():
                if MAIL_PARAMETERS_PATTERN%key in str(v):
                    parameters[k] = v.replace(MAIL_PARAMETERS_PATTERN%key,value)

        """parameters['page_view_in_browser'] = "%s/mails" \
             "?action=view&type=%s&id=%s&mail=%s&token=%s"%(host_web,mail_type,uuidValue,user_mail,token)
        parameters['page_unsuscribe'] = "%s/mails" \
              "?action=unsuscribe&type=%s&token=%s"%(host_web,mail_type,token)
        parameters['page_terms_of_use'] = '%s/terms-of-use'%(host_web)
        parameters['page_cgu']          = '%s/cgu'%(host_web)"""

        parameters_to_keep          = {}
        for key, value in parameters.items():
            if MAIL_PARAMETERS_PATTERN%key in parameters_to_specify:
                parameters_to_keep[key] = value

        print('Mail parameters:')
        for key, value in parameters_to_keep.items():
            print('   {:20} {}'.format(key,value))

        content                     = set_parameters(content,parameters_to_keep)

        parameters_not_specified    = list(set(get_mails_parameters(content)))

        if len(parameters_not_specified) != 0:
            log.error('Missing parameters %s for mail "%s"'%(','.join(parameters_not_specified),mail_type))
            return False

        """if not valid_signature:
            log.error('Invalid mail signature !')
            return False"""

        if is_mail_already_send(db,mail_type,parameters_to_keep,close_cnx=False,log=log):
            return False

        if is_blacklisted(db,user_mail,mail_type,close_cnx=False):
            return False

        # Send mail
        msg     = Message(title,
                    sender=sender,
                    recipients=[user_mail])
        msg.html = content
        current_app.extensions["mail"].send(msg)
        #api.mail.send(msg)

        # insert in history
        mail_type   = get_mail_type(mail_type)
        set_mail_history(db,mail_type,uuidValue,parameters_to_keep,close_cnx=False,log=log)
    if close_cnx:
        db.close()
    return True

def set_mail_history(db, mail_type,uuidValue,parameters,close_cnx=True,log=None):
    mail_type           = get_mail_type(mail_type)
    unique_parameters   = get_unique_parameters(parameters)
    query   = "INSERT INTO mails_history (uuid, mail_type, parameters, parameters_full) VALUES (%s,%s,%s,%s)"
    values  = (uuidValue,mail_type,json.dumps(unique_parameters),json.dumps(parameters))
    return db.execute_query(query,values,close_cnx=close_cnx)

def get_unique_parameters(parameter):
    unique_parameters = {}
    for key, value in parameter.items():
        if key[0:5] != 'page_': #key not in CoreW.CONSTANTS.keys() #TODO: check
            unique_parameters[key] = value
    return unique_parameters

def is_mail_already_send(db,mail_type,parameters, close_cnx=True,log=None):
    mail_type   = get_mail_type(mail_type)
    unique_parameters = get_unique_parameters(parameters)
    query   = "SELECT * from mails_history where mail_type = %s and parameters = %s"
    values  = (mail_type,json.dumps(unique_parameters))
    results = db.get_query_results(query,values,unique=False,close_cnx=close_cnx)
    return len(results) != 0

def is_blacklisted(db,user_mail,mail_type,close_cnx=True,log=None):
    mail_type   = get_mail_type(mail_type)
    query   = "SELECT * from mails_blacklist where mail_type = %s and mail = %s "
    values  = (mail_type,user_mail)
    results = db.get_query_results(query,values,unique=False,close_cnx=close_cnx)
    return len(results) != 0