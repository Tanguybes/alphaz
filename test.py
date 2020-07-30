# coding: utf8
# 

import os, requests, webbrowser, selenium
#from pystray import Icon, Menu, MenuItem
#from PIL import Image, ImageDraw
import sys
import pandas as pd

from libs.test_lib import execute_all_tests_auto

execute_all_tests_auto('tests/autos')

exit()
#rep = stitch.Stitch.getWebsites()

state = True

def on_clicked(icon, item):
    global state
    state = not item.checked

    if item.checked:
        print('start api')
        api.start()

def exitAlpha():
    icon.stop()
    
global icon
icon        = Icon('test name')
icon.icon   = Image.open("alpha.png")
icon.menu   = Menu(
        MenuItem('Alpha',None),
        MenuItem(
            'Running',
            on_clicked,
            checked=lambda item: state),
        MenuItem('Exit',exitAlpha),
    )
    

icon.run()