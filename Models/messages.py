from ..imports import *

class Messages(object):
    def __init__(self):
        self.debug          = False

    def debugPrint(self,string):
        if self.debug:
            print(__name__,string)

    def debugInfo(self,string):
        if self.debug:
            log.info(string)

    def switchDebug(self):
        self.debug = not self.debug