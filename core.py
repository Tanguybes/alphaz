import os, sys

from alphaz.models.main.core import AlphaCore
from alphaz.models.main.singleton import singleton

@singleton
class Core(AlphaCore):

    def __init__(self,file:str):
        super().__init__(file)

core = Core(__file__)
