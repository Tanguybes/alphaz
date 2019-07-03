# coding: utf8
# 

import os, requests, webbrowser, selenium

tmp         = 'C:\\tmp\\tmp.html' 
tmp_dir     = os.path.dirname(tmp)

#rep = stitch.Stitch.getWebsites()

from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import sys

state = True

def on_clicked(icon, item):
    global state
    state = not item.checked

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

exit()

s       = requests.Session()
res     = s.get(start_url)
cookies = dict(res.cookies)

# sending post request and saving response as response object 
r = s.post(url = login_url, data = data, verify=False, cookies=cookies) 
  
# extracting response text  
pastebin_url = r.text 

#res         = requests.get(start_url)

valid_answer = r.status_code == requests.codes.ok

if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)

with open(tmp,'w', encoding='utf-8') as f:
    f.write(pastebin_url)

print(pastebin_url)
print(valid_answer)

webbrowser.open(tmp)