import sys, imp, inspect, os, glob, copy
from ..models.watcher import ModuleWatcher
from typing import List, Dict

myself = lambda: inspect.stack()[1][3]

def get_modules_infos(name:str=None):
    from importlib_metadata import version
    import pkgutil
    data = {}
    for item in pkgutil.iter_modules():
        if name is not None and name.lower() != item.name.lower():
            continue
        try:
            data[item.name] = version(item.name)
        except:
            continue
    return data

def myself(fct=None):
    name = inspect.stack()[1][3]
    if fct:
        name = fct(name)
    return name

def reload_modules(root,log=None):
    root = root.replace("\\","\\\\")

    modules = [ x for x in sys.modules.values()]

    for module in modules:
        if root in str(module) and not 'core' in str(module).lower():
            if log:
                log.debug('   Reload %s'%module)
            try:
                imp.reload(module)
            except:
                pass

def watch_modules(roots: list=[],log=None):
    mw      = ModuleWatcher()
    roots   = [root.replace("\\","\\\\") for root in roots]

    modules = [ x for x in sys.modules.values()]
    for module in modules:
        for root in roots:
            if root in str(module) and not 'core' in str(module).lower():
                if log:
                    log.debug('Add <%s> to the watcher'%module)
                mw.watch_module(str(module))
    mw.start_watching()

def execute_cmd(cmd='',root=None,log=None):
    current_folder = os.getcwd()
    if root is not None:
        os.chdir(root)
    if log: log.info('Execute: <%s>'%cmd)
    os.system(cmd)
    os.chdir(current_folder) 

def get_directory_log_files(directory):
    return glob.glob(directory + os.sep + '*.log*')

def try_except(success, failure, *exceptions):
    try:
        return success()
    except exceptions or Exception:
        return failure() if callable(failure) else failure

def getsize(obj):
    """sum size of object & members."""
    if isinstance(obj, BLACKLIST):
        raise TypeError('getsize() does not take argument of type: '+ str(type(obj)))
    seen_ids = set()
    size = 0
    objects = [obj]
    while objects:
        need_referents = []
        for obj in objects:
            if not isinstance(obj, BLACKLIST) and id(obj) not in seen_ids:
                seen_ids.add(id(obj))
                size += sys.getsizeof(obj)
                need_referents.append(obj)
        objects = get_referents(*need_referents)
    return size

def get_attributes(obj):
    attributes = inspect.getmembers(obj, lambda a:not(inspect.isroutine(a)))
    return [a for a in attributes if not(a[0].startswith('__') and a[0].endswith('__'))]

def filter_kwargs(fct, args: list = [], kwargs: dict={}) -> dict:
    """Remove kwargs that are not in function kwargs

    Args:
        fct ([type]): [description]
        args (List): [description]
        kwargs (Dict): [description]

    Returns:
        [type]: [description]
    """
    fargs = inspect.getfullargspec(fct)
    kwargs = {x:y for x,y in kwargs.items() if x in fargs.args}
    return kwargs

def is_subtype(sub_type, parent_type):
    if sys.version_info >= (3, 7):
        if not hasattr(sub_type, '__origin__') or not hasattr(parent_type, '__origin__'):
            return False

        if sub_type.__origin__ != parent_type.__origin__:
            return False

        if isinstance(parent_type.__args__[0], type):
            return sub_type.__args__ == parent_type.__args__

        return True

    else:
        if not hasattr(sub_type, '__extra__') or not hasattr(parent_type, '__extra__'):
            return False

        if sub_type.__extra__ != parent_type.__extra__:
            return False

        if not parent_type.__args__ or parent_type.__args__ == sub_type.__args__:
            return True

    return False