import os, ast, json

from imports import *

class Stitch(object):
    name         = None
    path         = None
    configured   = False

    def __init__(self,name):
        self.name   = name
        self.path   = name.lower()

        websites    = Core.getWebsites()
        self.configured  = self.path in websites

    def init(self):
        path = Core.WEBSITES_PATH + os.sep + self.path + os.sep + Core.INIT_FILE
        if os.path.isfile(path):
            with open(path,'r') as f:
                content = f.read()
            content_dict = json.loads(content)
        
        if "element" in content_dict.keys():
            for key, element in content_dict["element"]:
                pass

    def get(self, *args):
        Core.DRIVER.get(args)

if __name__ == "__main__":
    stiki = Stitch('Stiki')

    stiki.init()

    print(stiki.configured)