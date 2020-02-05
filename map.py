# coding: utf8

import os, glob, argparse, copy, pickle
from shutil import copyfile, rmtree
from datetime import datetime

MAIN_APP = 'WSAlpha'

EXCLUDES            = []
FILES_EXTS_EXCLUDES = []
FILES_EXTS_INCLUDES = ['ppt','xls','pptx','doc','docx','pdf','txt','csv','xlsx']
for ext in copy.copy(FILES_EXTS_INCLUDES):
    FILES_EXTS_INCLUDES.append(ext.upper())

CONFIG_STRUCTURE    = {'date':None,'path':None,'ext':None,'name':None}

INDEX = 0
LIMIT = None
LEVEL = None

paths = {'MES Group':{
    'origin':'X:\OPER\IT',
    'output':'X',
    'folders':['AAB Groups','MES Group'],
    'level': 1
}}

def archive_object(object_to_save,filename):
    with open(filename, 'wb') as f:
        pickle.dump(object_to_save, f,protocol=pickle.HIGHEST_PROTOCOL)
    print('File %s archived'%filename)
        
def unarchive_object(filename):
    object_to_get= None
    try:
        with open(filename, 'rb') as f:
            object_to_get     = pickle.load(f)
    except:
        log.trace_show()
    return object_to_get

def get_views_files(dict_files, folder, root):
    current_folder  = folder.replace(root,'')
    level           = len([x for x in current_folder.split(os.sep) if x != ''])
    if LEVEL is not None and level > LEVEL:
        return dict_files
    
    dict_files[folder] = {}
    global INDEX
    global LIMIT
    
    print('Analyse %s ...'%folder)
    for exclude in EXCLUDES:
        exc_rule =  os.sep + exclude + os.sep
        if exc_rule in folder:
            return dict_files
    
    files_path = glob.glob(folder + os.sep + '*')
    for file_path in files_path:
        #print('   ....',file_path)
        try:
            time                    = os.path.getmtime(file_path)
            date                    = datetime.fromtimestamp(time)
        except:
            print('error with %s'%file_path)
            continue
        rep             = not '.' in file_path
        
        #print('      >',file_path)
        
        if os.path.isdir(file_path):
            dict_files      = get_views_files(dict_files, file_path, root)
        else:
            ext = '' if not '.' in file_path.split(os.sep)[-1] else file_path.split(os.sep)[-1].split('.')[1]
            if ext in FILES_EXTS_INCLUDES:
                file_name   = file_path.split(os.sep)[-1]
                arbor       = file_path.replace(root + os.sep,'').split(os.sep)[:-1]
                #print(' ----- ',file_name)
                """
                i = 0
                config = dict_files[folder]
                for el in arbor:
                    if not el in config:
                        config[el] = {}
                    config = config[el]
                    i += 1"""
                
                dict_files[folder][file_name]               = copy.deepcopy(CONFIG_STRUCTURE)
                
                dict_files[folder][file_name]['date']       = date.strftime("%m/%d/%Y %H:%M:%S")
                dict_files[folder][file_name]['path']       = file_path.replace(root + os.sep,'')
                dict_files[folder][file_name]['full_path']  = file_path
                dict_files[folder][file_name]['arbor']      = arbor
                dict_files[folder][file_name]['ext']        = '' if len(file_name.split('.')) == 1 else file_name.split('.')[1]
                dict_files[folder][file_name]['name']       = file_name.split('.')[0]
            else:
                if not ext in FILES_EXTS_EXCLUDES:
                    FILES_EXTS_EXCLUDES.append(ext)
        INDEX += 1
        
        if not LIMIT is None and INDEX > LIMIT:
            return dict_files
    return dict_files

def cmd(cmd_str):
    print('   executing: %s'%cmd_str)
    os.system(cmd_str)
    
files_rep   = 'C:\Git\WSAlpha\Areas\Tools\Views\Documentation\\Networks'
end_line    = '|}\n'

def save_files(dict_files,output,folders,archive_root):
    output_full = output + os.sep + os.sep.join(folders)

    target_url = 'http://localhost:55835/Tools/Documentation/Index?network='+output_full.replace('\\','/').replace(' ','%20')+'&path='
    
    # WSAlpha
    HEADS = {'name':'Name','ext':'Extension','arbor':'Arborescence','date':'Last modification','full_path':'Path'}
    """for key, text in HEADS.items():
        head += '<th>%s</th>\n'%text"""

    cshtml_file_path = archive_root + os.sep + 'files.cshtml'
    with open(cshtml_file_path,'w') as f:
        f.write('')
        
    # Stiki
    head_table = """
! scope=col | Name
! scope=col | Extension
! scope=col | Last modification
! scope=col | Path
|-
    """
    close = False
    paths, arbor = [], {}
    content = ''
    
    stiki_file_path = archive_root + os.sep+ 'files.txt'
    with open(stiki_file_path,'w') as f:
        f.write('')
    
    i, count = 0, len(dict_files)
    for folder, file_config in dict_files.items():
        # WSALPHA
        core = ''
        for file_path, config in file_config.items():
            if 'path' in config:
                core += '<tr>'
                for key in HEADS:
                    if key == 'arbor':
                        value = os.sep.join(config[key])
                    elif key == 'name':
                        value = '<a href="%s" target="_blank">%s</a>'%(config['full_path'],config['name'])
                    else:
                        value = config[key]
                    core += '<td align="left">%s</td>\n'%value
                core += '</tr>'
        
        core = core.replace('@','&#64;')
        
        try:
            with open(cshtml_file_path, "a",encoding='utf-8') as myfile:
                myfile.write(core)
        except Exception as ex:
            lines= core.split('\n')
            for line in lines:
                try:
                    with open('tmp.txt','a',encoding='utf-8') as tmp_file:
                        tmp_file.write(line)
                except:
                    print(line)
                    exit()
            print(core)
            exit()
            
        # STIKI
        folder = folder.replace(root + os.sep,'')
        arbore = folder.split(os.sep)
        content = ''
        if not folder in paths:
            if close and len(file_config.items()) != 0 and not '|}' in content[-4:]:
                content += '|}\n'
            close = False

            paths.append(folder)
            
            lvl = len(arbore) * '='
            """if len(arbore) <= 5:
                content += '%s %s %s\n'%(lvl,arbore[-1],lvl)
            else:
                content += '%s %s\n'%((len(arbore) - 5)*'#',arbore[-1])"""
            content += '= %s ='%folder
            
            if len(file_config.items()) != 0:
                content += """
                {| border="1" width="100%" align="center" style=""
                |-
                """
                content += head_table
                
                close = True
                
        for file_path, config in file_config.items():
            m = len(config['arbor'])
            
            content += '||[%s%s %s]\n'%(target_url,config['full_path'].replace(' ','%20'),file_path)
            content += '||%s\n'%(config['ext'])
            content += '||%s\n'%(config['date'])
            content += '||%s\n'%(config['full_path'])
            content += '|-\n'
        
        if len(file_config.items()) != 0 and close and not '|}' in content[-4:]:
            content += '|}\n'
            
        with open(stiki_file_path, "a",encoding='utf-8') as myfile:
            myfile.write(content)
    
        i += 1
        print('%s / %s'%(i,count)) 

def pack(root,folders,output,files_rep,save=False):
    if not os.path.exists(root):
        print('Repository %s does not exist'%root)
        
    archive_root    = files_rep + os.sep + output + os.sep + os.sep.join(folders)
    if not os.path.exists(archive_root):
        os.makedirs(archive_root)
        
    dict_files      = {}
    with open('tmp.txt','w') as tmp_file:
        tmp_file.write('')
        
    archive_file    = archive_root + os.sep + 'dict_files.pkl'
           
    # Views files
    if save:
        dict_files  = get_views_files(dict_files, root, root)
        archive_object(dict_files,archive_file)
    else:
        dict_files = unarchive_object(archive_file)
                
        save_files(dict_files, output,folders,archive_root)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Publish WSALPHA', description='WSALPHA - publishing tool', epilog='WSALPHA')
    parser.add_argument('--save','-s',action='store_true')
    
    args                = parser.parse_args()

    for name, path_config in paths.items():
        output          = path_config['output']
        root            = path_config['origin'] + os.sep + os.sep.join(path_config['folders']) #os.getcwd()
        
        if not 'level' in path_config:
            pass
        elif path_config['level'] == 1:
            dirs = glob.glob(root + os.sep + '*')
            for dir in dirs:
                if os.path.isdir(dir):
                    folders = path_config['folders']
                    folders.append(dir.replace(root,''))
                    pack(dir,folders,output,files_rep,save=args.save)
                    print(FILES_EXTS_EXCLUDES)
                    exit()