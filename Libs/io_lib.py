import requests, json, os, pickle
from lxml.html import fromstring

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def ensure_file(filename):
    ensure_dir(filename)
    # create file is not exist
    with open(filename,"w") as f:
        f.write("")

def save_as_json(filename,data,verbose): 
    ensure_file(filename)
    if verbose:
        print('Write json file to %s'%filename)

    # Writing JSON data
    with open(filename, 'w') as f:
        json.dump(data, f)

def get_proxies():
    url         = 'https://free-proxy-list.net/'
    response    = requests.get(url)
    parser      = fromstring(response.text)
    proxies     = set()
    for i in parser.xpath('//tbody/tr')[:10]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies

def archive_object(object_to_save,filename):
    with open(filename, 'wb') as f:
        pickle.dump(object_to_save, f,protocol=pickle.HIGHEST_PROTOCOL)
        
def unarchive_object(filename):
    object_to_get= None
    try:
        with open(filename, 'rb') as f:
            object_to_get     = pickle.load(f)
    except Exception as ex:
        print(ex)
        #log.trace_show()
    return object_to_get