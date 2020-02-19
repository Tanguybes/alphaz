from selenium import webdriver
from glob import glob
import os

class Core:
    INIT            = False

    INIT_FILE       = "init.json"
    WEBSITES_PATH   = 'websites'
    DRIVER_PATH     = 'web-drivers/chromedriver.exe'

    CAPABILITIES    = { 'chromeOptions':  { 'useAutomationExtension': False}}

    DRIVER          = None
    ROOT_PATH       = ""

    @staticmethod
    def init():    
        print('Core initialization')
        Core.ROOT_PATH  = os.path.dirname(__file__)
        Core.DRIVER     = webdriver.Chrome(Core.ROOT_PATH + os.sep + Core.DRIVER_PATH, desired_capabilities = Core.CAPABILITIES)

    @staticmethod
    def getWebsites():
        results     = glob(Core.WEBSITES_PATH + os.sep + "*")
        websites    = [os.path.basename(x) for x in results if os.path.isdir(x)]
        return websites

if not Core.INIT:
    Core.init()