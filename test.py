# coding: utf8
# 

import os, requests, webbrowser, selenium

from selenium import webdriver

tmp         = 'C:\\tmp\\tmp.html' 
tmp_dir     = os.path.dirname(tmp)
start_url   = 'http://stiki.cr2.st.com/STIKI/index.php'

login_url   = "http://stiki.cr2.st.com/STIKI/index.php?title=Special:UserLogin&action=submitlogin&type=login&returnto=Main+Page"

# data to be sent 
data = {'wpName1':"duranda1", 
        'wpPassword1':'STAdama21it$7', 
        'wpRemember':''} 
        
DRIVER_PATH = 'web-drivers/chromedriver.exe'

SUBMIT_BUTTON = 'wpLoginAttempt'

capabilities = { 'chromeOptions':  { 'useAutomationExtension': False}}
driver = webdriver.Chrome(DRIVER_PATH, desired_capabilities = capabilities)
driver.get(login_url)

for key, value in data.items():
    #driver.find_element_by_id(MAIL).send_keys(user_name)
    elem_pass = driver.find_element_by_id(key)
    elem_pass.send_keys(value)
#elem_pass.submit()
driver.find_element_by_id(SUBMIT_BUTTON).click()

input('end ?')
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