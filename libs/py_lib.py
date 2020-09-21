import sys, imp, inspect, os, glob, copy
from ..models.watcher import ModuleWatcher

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

def watch_modules(roots: [],log=None):
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