from ..logger import AlphaLogger
import inspect

from ...libs import py_lib

class AlphaClass:
    def __init__(self, *args, log:AlphaLogger = None, **kwargs):
        self.init_args = {'args':args, 'kwargs':kwargs}
        self.children = list()

        self.log: AlphaLogger       = log

        self._debugs = []
        self._infos = []
        self._errors = []
        self._warnings = []

    def make_child(self, child_cls, *args, **kwargs):
        if args is None:
            args = self.init_args['args']
        if kwargs is None:
            kwargs = self.init_args['kwargs']
        child = child_cls(self, *args, **kwargs)
        self.children.append(child)
        return child

    def get_attributes(self):
        return py_lib.get_attributes()

    def to_json(self):
        return self.get_attributes()

    def debug(self,message,ex=None): 
        if self.log is not None:
            if len(self._debugs) != 0:
                for deb in self._debugs:
                    self.log.debug(info,ex=ex)
                self._debugs = []
            self.log.debug(message,ex=ex)
        else:
            self._debugs.append(message)

    def info(self,message,ex=None):
        if self.log is not None:
            if len(self._infos) != 0:
                for info in self._infos:
                    self.log.info(info,ex=ex)
                self._infos = []
            self.log.info(message,ex=ex)
        else:
            self._infos.append(message)

    def warning(self,message,ex=None):
        if self.log is not None:
            if len(self._warnings) != 0:
                for msg in self._warnings:
                    self.log.warning(msg,ex=ex)
                self._warnings = []
            self.log.warning(message,ex=ex)
        else:
            self._warnings.append(message)

    def error(self,message,out=False,ex=None):
        for info in self._infos:
            print('   INFO: %s'%info)
        if self.log is not None:
            self.log.error(message,ex=ex)
        else:
            print('   ERROR: %s'%message)
        if out: exit()
