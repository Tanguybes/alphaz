import sys, imp, inspect

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