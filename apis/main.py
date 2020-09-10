import sys, os, inspect, copy

from ..libs import dict_lib
from ..utils.logger import AlphaLogger

def get_routes_infos(log:AlphaLogger=None) -> dict:
    """Get all apis routes with informations

    Args:
        log ([AlphaLogger], optional): [description]. Defaults to None.

    Returns:
        dict: [description]
    """
    modules = {}
    routes = {}

    if log: log.info('Getting %s routes from loaded modules'%('alphaz' if not all else "all"))

    routes_dict = {}
    categories = []
    categories_routes = {}

    imported_modules = copy.copy(sys.modules)
    for key, module in imported_modules.items():

        current_project = os.getcwd().split(os.sep)[-1] in str(module)
        if 'alphaz' in key or current_project:
            try:
                functions_list  = [o for o in inspect.getmembers(module) if inspect.isfunction(o[1])]
            except:
                continue

            #if log: log.debug('Loading module from %s'%key)

            for function_tuple in functions_list:
                function_name, fct = function_tuple

                fct_n = getattr(module,function_name)
                wraps = inspect.unwrap(fct)

                if 'route.' in str(wraps) and hasattr(fct_n,'_kwargs'):
                    path        = fct_n._kwargs['path']
                    if path == '/': continue

                    #print(function_name,wraps,wraps.__name__,inspect.signature(fct,follow_wrapped=False),inspect.signature(wraps),inspect.unwrap(wraps))

                    paths  = [ x for x in path.split('/') if x.strip() != '']
                    if len(paths) == 1:
                        paths = ['root',paths[0]]

                    category = fct_n._kwargs['category']
                    if not category in categories:
                        categories.append(category)
                    if not category in categories_routes:
                        categories_routes[category] = []
                    categories_routes[category].append(path)

                    out         = dict_lib.get_nested_dict_from_list(paths)
                    routes_dict = dict_lib.merge_dict(routes_dict,out)

                    if not path in routes:            routes[path] = []

                    routes[path] = {
                        'module':key,
                        'paths':paths,
                        'name':function_name,
                        'arguments':{x:y if x != 'parameters' else [j.__dict__ for j in y] for x,y in fct_n._kwargs.items()}
                    }

    modules['routes_list']          = routes.keys()
    modules['routes']               = routes
    modules['routes_paths']         = routes_dict
    modules['categories']           = categories
    modules['categories_routes']    = categories_routes

    return modules