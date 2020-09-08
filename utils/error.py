
def get_message_from_name(name):
    return name.replace('_',' ').capitalize()

class AlphaException(Exception):

    def __init__(self, name,message=None):
        self.name           = name
        self.message        = message or get_message_from_name(name)
        super().__init__(self.message)

class AlphaError:
    def __init__(self,name,message=None,value=None):
        self.name           = name
        self.message        = message or get_message_from_name(name)
        self.value          = value