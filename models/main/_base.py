from typing import Dict, List
from ..logger import AlphaLogger
import inspect

from ...libs import py_lib

class AlphaClass:
    def __init__(self, *args, log:AlphaLogger = None, **kwargs):
        self.init_args: dict = {'args':args, 'kwargs':kwargs}
        self.children: list = []

        self.log: AlphaLogger       = log

        self.__piles: Dict[str, List[str]] = {}

    def make_child(self, child_cls, *args, **kwargs):
        if args is None:
            args = self.init_args['args']
        if kwargs is None:
            kwargs = self.init_args['kwargs']
        child = child_cls(self, *args, **kwargs)
        self.children.append(child)
        return child

    def get_attributes(self):
        return py_lib.get_attributes(self)

    def to_json(self):
        return self.get_attributes()

    def __log(self, stack, message, ex=None):
        if not stack in self.__piles:
            self.__piles[stack] = []
        pile = self.__piles[stack]

        if self.log is not None:
            method = getattr(self.log, stack)
            if len(pile) != 0:
                for deb in pile:
                    method(deb,ex=ex)
                stack = []
            method(message,ex=ex)
        else:
            pile.append(message)

    def debug(self,message,ex=None): 
        self.__log(inspect.stack()[0][3], message=message, ex=ex)

    def info(self,message,ex=None):
        self.__log(inspect.stack()[0][3], message=message, ex=ex)

    def warning(self,message,ex=None):
        self.__log(inspect.stack()[0][3], message=message, ex=ex)

    def error(self,message,out=False,ex=None):
        self.__log(inspect.stack()[0][3], message=message, ex=ex)
        if out: exit()
