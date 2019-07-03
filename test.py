# coding: utf8
# 

import os, requests, webbrowser, selenium

tmp         = 'C:\\tmp\\tmp.html' 
tmp_dir     = os.path.dirname(tmp)

#rep = stitch.Stitch.getWebsites()

import pystray
from PIL import Image, ImageDraw
icon = pystray.Icon('test name')

width = 25
height = 25
color1 = "red"
color2 = "blue"

def create_image():
    # Generate an image and draw a pattern
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (width // 2, 0, width, height // 2),
        fill=color2)
    dc.rectangle(
        (0, height // 2, width // 2, height),
        fill=color2)

    return image

icon.icon = create_image()

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