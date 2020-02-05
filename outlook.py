# import the win32com library
import win32com.client
 
# get Outlook application object
Outlook = win32com.client.Dispatch("Outlook.Application")
 
# get the Namespace / Session object
namespace   = Outlook.Session
inbox       = namespace.GetDefaultFolder(6)

messages    = inbox.Items
 
# get message contents
for message in messages:
    try:
        sender      = message.Sender
        receiver    = message.To
        cc          = message.Cc
        subject     = message.Subject
        body        = message.Body
        print(sender)
    except:
        pass