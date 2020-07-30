import glob, os, shutil

sep = os.sep

def folders_list(root,path):
    return [x for x in path.replace(root,'').split(sep) if x != '']

def copy_files(root_source, root_dest, folders, verbose=False,action=False,infos={},exts_excludes={},dirs_excludes={}):
    if not 'nb' in infos:
        infos['nb'] = 0

    folder = root_source + sep + sep.join(folders) + sep + '*'
    files  = glob.glob(folder)
    
    for file_name in files:
        if os.path.isfile(file_name):
            ext = ''
            try:
                ext         = file_name.split('.')[1]
            except:
                pass

            if not ext in exts_excludes:
                new_folders = folders_list(root_source,file_name)
                infos = copy_file(root_source, root_dest, new_folders[:-1], new_folders[-1],
                    verbose=verbose,action=action,infos=infos)
        else:
            new_folders = folders_list(root_source,file_name)
            new_folder  = file_name.split(os.sep)[-1]
            if not new_folder in dirs_excludes:
                copy_files(root_source, root_dest, new_folders,verbose=verbose,action=action,infos=infos)
    return infos

def copy_file(root_source, root_dest, folders, file_name,verbose=False,action=False,infos={}):
    if not 'nb' in infos:
        infos['nb'] = 0

    relative_path   = sep.join(folders) + sep + file_name
    source          = root_source + sep + relative_path
    new_root        = root_dest + sep + sep.join(folders)
    
    dest            = new_root + sep + file_name
    
    try:
        new, up_to_date = not os.path.exists(dest), False
        if not new:
            source_modification = os.path.getmtime(source)
            dest_modification   = os.path.getmtime(dest)
            up_to_date          = source_modification <= dest_modification

        if  (new or not up_to_date):
            action_str  =   None
            if action:
                if not os.path.exists(new_root):
                    os.makedirs(new_root)
                shutil.copy(source,dest)
                
                if   new:               action_str = 'ADD'
                elif not up_to_date:    action_str = 'MAJ'
            else:   
                if   new:               action_str = 'NEW'
                elif not up_to_date:    action_str = 'OLD'

            if action_str is not None:
                infos['nb'] += 1
                if verbose:
                    print('  {}  {:50} from {:40} to {}'.format(action_str,relative_path,root_source, root_dest))

    except Exception as ex:
        print("ERROR:",ex)
    return infos