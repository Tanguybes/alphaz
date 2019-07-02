# coding: utf8
# 

import os, requests, webbrowser, selenium

from stitch import stitch

tmp         = 'C:\\tmp\\tmp.html' 
tmp_dir     = os.path.dirname(tmp)

# data to be sent 
rep = stitch.Stitch.getWebsites()
print(rep)

input('end ?')
exit()
driver.get(login_url)
for key, value in data.items():
    #driver.find_element_by_id(MAIL).send_keys(user_name)
    elem_pass = driver.find_element_by_id(key)
    elem_pass.send_keys(value)
#elem_pass.submit()
driver.find_element_by_id(SUBMIT_BUTTON).click()


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