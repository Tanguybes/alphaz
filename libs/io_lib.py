import requests, json, re, os, pickle, pathlib
from lxml.html import fromstring

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if directory != '' and not os.path.exists(directory):
        os.makedirs(directory)

def ensure_file(filename):
    ensure_dir(filename)

    if not os.path.exists(filename):
        # create file is not exist
        with open(filename,"w") as f:
            f.write("")

def save_as_json(filename,data,verbose=False):
    ensure_file(filename)
    if verbose:
        print('Write json file to %s'%filename)

    # Writing JSON data
    json_content = json.dumps(data, default=lambda x: None)
    with open(filename, 'w') as f:
        f.write(json_content)
        #json.dump(data, f)

def read_json(file_path):
    original = {}

    with open(file_path,'r') as f:
        original = f.read()
    # save state
    states = []
    text = original
    
    # save position for double-quoted texts
    for i, pos in enumerate(re.finditer('"', text)):
        # pos.start() is a double-quote
        p = pos.start() + 1
        if i % 2 == 0:
            nxt = text.find('"', p)
            states.append((p, text[p:nxt]))

    # replace all weired characters in text
    while text.find(',,') > -1:
        text = text.replace(',,', ',null,')
    while text.find('[,') > -1:
        text = text.replace('[,', '[null,')

    # recover state
    for i, pos in enumerate(re.finditer('"', text)):
        p = pos.start() + 1
        if i % 2 == 0:
            j = int(i / 2)
            nxt = text.find('"', p)
            # replacing a portion of a string
            # use slicing to extract those parts of the original string to be kept
            text = text[:p] + states[j][1] + text[nxt:]
   
    converted = json.loads(text) # error stems from here
    return converted

def get_proxies(nb=None):
    url         = 'https://free-proxy-list.net/'
    response    = requests.get(url)
    parser      = fromstring(response.text)
    proxies     = set()

    #selects     = parser.xpath('//html/body/section[1]/div/div[2]/div/div[1]/div[1]/div/label/select')

    for i in parser.xpath('//tbody/tr'):
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies

def archive_object(object_to_save,filename, ext='dmp'):
    ensure_dir(filename)
    if ext is not None and pathlib.Path(filename).suffix == '':
        filename = filename + '.' + ext
    with open(filename, 'wb') as f:
        pickle.dump(object_to_save, f,protocol=pickle.HIGHEST_PROTOCOL)
        
def unarchive_object(filename, ext='dmp'):
    if ext is not None and pathlib.Path(filename).suffix == '':
        filename = filename + '.' + ext
    object_to_get = None
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            object_to_get     = pickle.load(f)
            #log.trace_show()
    return object_to_get

def print_dict(dictio,level=1):
    for key, value in dictio.items():
        if type(value) == dict:
            print("{} {:20}".format(level*'  ',key))
            print_dict(value,level + 1)
        else:
            print("{} {:20} {}".format(level*'  ',key,value))

    