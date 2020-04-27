import os

def get_path_name(path,ext=False):
    name = os.path.basename(path)
    if ext:
        return name
    return '.'.join(name.split('.')[:-1])