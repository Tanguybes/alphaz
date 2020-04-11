import sys, imp, inspect, os
from ..models.watcher import ModuleWatcher

def reload_modules(root,verbose=True):
    root = root.replace("\\","\\\\")

    for module in sys.modules.values():
        if root in str(module) and not 'core' in str(module).lower():
            if verbose:
                print('   Reload %s'%module)
            try:
                imp.reload(module)
            except:
                pass

def watch_modules(roots: [],verbose=True):
    mw      = ModuleWatcher()
    roots   = [root.replace("\\","\\\\") for root in roots]

    for module in sys.modules.values():
        for root in roots:
            if root in str(module) and not 'core' in str(module).lower():
                if verbose:
                    print('   Add %s to the watcher'%module)
                mw.watch_module(str(module))
    mw.start_watching()

def execute_cmd(cmd='',root=None):
    current_folder = os.getcwd()
    if root is not None:
        os.chdir(root)
    print('   Execute: ',cmd)
    os.system(cmd)
    os.chdir(current_folder) 