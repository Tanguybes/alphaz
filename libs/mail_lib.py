import smtplib, socks

import hashlib, re, os, datetime
from flask_mail import Message
from flask import current_app
import uuid
from . import sql_lib

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
                log.error('Cannot find mail content at %s'%(file_name))
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

    with open('/home/truegolliath/svntools/aurele/mails/debug.html','w') as f:
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
            content = content.replace('{{%s}}'%parameter,str(value))
    return content

def get_parameters(content):
    title_regex = r'\{\{.*?\}\}'
    founds = re.findall(title_regex,content)
    return founds

def send_mail(host_web,mail_path,mail_type,parameters_list,sender,cnx,log,key_signature="<alpha mail>",
        default_tile='',close_cnx=True):
    content                 = get_mail_content(mail_path,mail_type,log)
    parameters_to_specify   = get_parameters(content)

    if content is None:
        return False

    valid_signature     = key_signature in str(content) 
    title               = get_title(content,default=default_tile)

    now = datetime.datetime.now()
    year = now.year
    month = now.month
    hour = now.hour
    minute = now.minute
    second=now.second

    for parameters in parameters_list:
        for key, value in parameters.items():
            if '{{%s}}'%key in title:
                title = title.replace('{{%s}}'%key,value)

        uuidValue = str(uuid.uuid4())

        if not 'mail' in parameters.keys():
            log.error('Missing parameter <mail> for sending mail !')
            return False

        user_mail           = parameters['mail']
        token               = get_mail_token(user_mail)

        parameters['year']                  = year
        parameters['page_view_in_browser'] = "%s/mails" \
             "?action=view&type=%s&id=%s&mail=%s&token=%s"%(host_web,mail_type,uuidValue,user_mail,token)
        parameters['page_unsuscribe'] = "%s/mails" \
              "?action=unsuscribe&type=%s&token=%s"%(host_web,mail_type,token)
        parameters['page_terms_of_use'] = '%s/terms-of-use'%(host_web)
        parameters['page_cgu']          = '%s/cgu'%(host_web)

        parameters_to_keep          = {}
        for key, value in parameters.items():
            if '{{%s}}'%key in parameters_to_specify:
                parameters_to_keep[key] = value

        """for key, value in parameters.items():
            print('   {:20} {}'.format(key,value))"""

        content                     = set_parameters(content,parameters_to_keep)

        parameters_not_specified    = get_parameters(content)

        if len(parameters_not_specified) != 0:
            log.error('Missing parameters %s for mail "%s"'%(','.join(parameters_not_specified),mail_type))
            return False

        if not valid_signature:
            log.error('Invalid mail signature !')
            return False

        if is_mail_already_send(cnx,mail_type,parameters_to_keep,close_cnx=False,log=log):
            return False

        if is_blacklisted(cnx,user_mail,mail_type,close_cnx=False,log=log):
            return False

        # Send mail
        msg = Message(title,
                    sender=sender,
                    recipients=[user_mail])
        msg.html = content
        current_app.extensions["mail"].send(msg)

        # insert in history
        set_mail_history(cnx,mail_type,uuidValue,parameters_to_keep,close_cnx=False,log=log)
    if close_cnx:
        cnx.close()
    return True

def set_mail_history(cnx, mail_type,uuidValue,parameters,close_cnx=True,log=None):
    unique_parameters = get_unique_parameters(parameters)
    query   = "INSERT INTO mails_history (uuid, mail_type, parameters, parameters_full) VALUES (%s,%s,%s,%s)"
    values  = (uuidValue,mail_type,str(unique_parameters),str(parameters))
    return sql_lib.execute_query(cnx, query,values,close_cnx=close_cnx,log=log)

def get_unique_parameters(parameter):
    unique_parameters = {}
    for key, value in parameter.items():
        if key[0:5] != 'page_': #key not in CoreW.CONSTANTS.keys() #TODO: check
            unique_parameters[key] = value
    return unique_parameters

def is_mail_already_send(cnx,mail_type,parameters, close_cnx=True,log=None):
    unique_parameters = get_unique_parameters(parameters)
    query   = "SELECT * from mails_history where mail_type = %s and parameters = %s"
    values  = (mail_type,str(unique_parameters))
    results = sql_lib.get_query_results(cnx,query,values,unique=False,close_cnx=close_cnx,log=log)
    return len(results) != 0

def is_blacklisted(cnx,user_mail,mail_type,close_cnx=True,log=None):
    query   = "SELECT * from mails_blacklist where mail_type = %s and mail = %s "
    values  = (mail_type,user_mail)
    results = sql_lib.get_query_results(cnx,query,values,unique=False,close_cnx=close_cnx,log=log)
    return len(results) != 0