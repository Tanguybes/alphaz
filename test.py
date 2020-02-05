# coding: utf8
# 

import os, requests, webbrowser, selenium
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import sys

import pandas as pd

import api

with open('tns.ora','r') as f:
    content = f.read()

print(content)
exit()

tmp         = 'C:\\tmp\\tmp.html' 
tmp_dir     = os.path.dirname(tmp)

#rep = stitch.Stitch.getWebsites()

import cx_Oracle

dsn_tns = cx_Oracle.makedsn('crx033.cro.st.com', '1525', 'fcm')
conn    = cx_Oracle.connect('Alphadevadm','STCrollesDev_38',dsn_tns)
cursor    = conn.cursor()

cursor.execute('select * from TABLES')

col_names = []
for i in range(0, len(cursor.description)):
    col_names.append(cursor.description[i][0])

group = []
for row in cursor:
    group.append(row)

dataset = pd.DataFrame(group,columns=col_names)

print(dataset)
print(col_names)

conn.close()
exit()

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