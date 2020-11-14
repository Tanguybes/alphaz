from ..logger import AlphaLogger

class AlphaClass:
    def __init__(self,log:AlphaLogger = None):
        self.log: AlphaLogger       = log
        self._infos = []
        self._errors = []
        self._warnings = []

    def info(self,message):
        if self.log is not None:
            if len(self._infos) != 0:
                for info in self._infos:
                    self.log.info(info)
                self._infos = []
            self.log.info(message)
        else:
            self._infos.append(message)

    def warning(self,message):
        if self.log is not None:
            if len(self._warnings) != 0:
                for msg in self._warnings:
                    self.log.warning(msg)
                self._warnings = []
            self.log.warning(message)
        else:
            self._warnings.append(message)

    def error(self,message,out=False):
        for info in self._infos:
            print('   INFO: %s'%info)
        if self.log is not None:
            self.log.error(message)
        else:
            print('   ERROR: %s'%message)
        if out: exit()