import smtplib, socks

import win32com.client as win32

FROM        = 'aurele.durand@st.com'
PASSWORD    = 'STAdama22it$7'


TOS     = ['nordine.ben-dahmane@st.com','aurele.durand@st.com','patrice.guil@st.com','marion.giraudi@st.com','sandrine.scatamacchia@st.com','eve.mietton@st.com','henri.banvillet@st.com',
'cedric.herchin-paul@st.com', 'denise.dussert-rosset@st.com', 'frederic.romuald@st.com', 'jeremy.georges2@st.com' , 'julien.rohmer@st.com', 'mathieu.lagoutte@st.com', 'osman.attal@st.com', 'rania.salem@st.com', 'sylvain.moschetti@st.com']

#TOS     = ['aurele.durand@st.com']
TO      = ';'.join(TOS)

proxy_host = '165.225.76.32'
proxy_port = '80'

def mail2(subject,body,bodyHtml=None,attachments=[]):
    outlook = win32.Dispatch('outlook.application')
    mail = outlook.CreateItem(0)
    mail.To = TO 
    mail.Subject = subject
    mail.Body = body
    mail.HTMLBody = bodyHtml if bodyHtml is not None else body #this field is optional

    # To attach a file to the email (optional):
    if len(attachments) != 0:
    #attachment  = "Path to the attachment"
        for attachment in attachments:
            mail.Attachments.Add(attachment)

    mail.Send()

def mail():
    receivers = [TO]

    message = """From: From Person <from@fromdomain.com>
    To: To Person <to@todomain.com>
    Subject: SMTP e-mail test

    This is a test e-mail message.
    """
    
    
    socks.setdefaultproxy(socks.HTTP, proxy_host, proxy_port)
    socks.wrapmodule(smtplib)

    try:
       smtpObj = smtplib.SMTP('SMTP.office365.com')
       smtpObj.sendmail(FROM, receivers, message)         
       print ("Successfully sent email")
    except Exception as ex:
       print ("Error: unable to send email: ",ex)
    
if __name__ == '__main__':
    mail2()