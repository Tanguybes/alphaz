from fbchat import Client
from fbchat.models import *

client = Client("durand.aurele@gmail.com", "Adama14fb$7")

print("Own id: {}".format(client.uid))

client.send(Message(text="Hi me!"), thread_id=client.uid, thread_type=ThreadType.USER)

client.logout()
