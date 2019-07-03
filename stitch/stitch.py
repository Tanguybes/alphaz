import os, ast, json

from imports import *

class Stitch(object):
    name        = None
    path        = None
    configured  = False

    elements    = {}

    def __init__(self,name):
        self.name       = name
        self.path       = name.lower()

        websites        = Core.getWebsites()
        self.configured = self.path in websites

    def process(self, file_name):
        path = Core.WEBSITES_PATH + os.sep + self.path + os.sep + file_name

        if os.path.isfile(path):
            with open(path,'r') as f:
                content = f.read()
            content_dict = json.loads(content)

        root_keys = content_dict.keys()
        
        for key in root_keys:
            properties = content_dict[key]

            if key == "elements":
                for key, properties in properties.items():
                    self.elements[key] = Element(key, properties)
            elif key == "url":
                self.get(properties)
            elif key == "set":
                for el in properties:
                    name = list(el.keys())[0]
                    value = el[name]
                    self.elements[name].value = value

                    elem_pass = self.getById(name)
                    elem_pass.send_keys(value)
            elif key == "click":
                for name in properties:
                    self.getById(name).click()

    def getById(self,name):
        return Core.DRIVER.find_element_by_id(name)

    def get(self, *args):
        Core.DRIVER.get(args[0])

if __name__ == "__main__":
    stiki = Stitch('Stiki')
    stiki.process(Core.INIT_FILE)