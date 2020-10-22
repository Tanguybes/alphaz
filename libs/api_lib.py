
import sys, os, inspect, copy

from ..libs import dict_lib
from ..utils.logger import AlphaLogger

from ..models.api._converters import jsonify_database_models
from ..models.api._converters import jsonify_data

MODULES = {}

def get_columns_values_output(objects:list,columns:list=None) -> dict:
    """ Get output with columns / values format

    Args:
        objects (list): [description]
        columns (list): [description]

    Returns:
        dict: [description]
    """
    if len(objects) == 0:
        return {}

    results = jsonify_data(objects)

    if columns and len(columns) != 0:
        results = [{key:value for key, value in result.items() if key in columns} for result in results]
    else:
        columns = list(results[0].keys())

    data                = {}
    data['columns']     = [x for x in columns if x in results[0]]
    data['values']      = [[x[y] for y in columns if y in x] for x in results]
    data['values_nb']   = len(data['values'])
    return data

def get_routes_infos(log:AlphaLogger=None,categories=None,routes=None,reload=False) -> dict:
    """Get all apis routes with informations

    Args:
        log ([AlphaLogger], optional): [description]. Defaults to None.

    Returns:
        dict: [description]
    """

    if len(MODULES) != 0 and not reload: 
        return MODULES

    routes_configurations = {}

    if log: log.debug('Getting %s routes from loaded modules'%('alphaz' if not all else "all"))

    routes_dict = {}
    categories_routes_list = []
    categories_routes = {}
    loaded_paths = []

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

                    if path in loaded_paths:
                        log.error('Path <%s> from <%s> for method <%s> already loaded in api'%(path,key,function_name))
                    loaded_paths.append(path)

                    if path == '/': continue
                    if routes is not None and path not in routes: continue

                    #print(function_name,wraps,wraps.__name__,inspect.signature(fct,follow_wrapped=False),inspect.signature(wraps),inspect.unwrap(wraps))

                    paths  = [ x for x in path.split('/') if x.strip() != '']
                    if len(paths) == 1:
                        paths = ['root',paths[0]]

                    category = fct_n._kwargs['category']

                    if categories is not None and category not in categories: continue

                    if not category in categories_routes_list:
                        categories_routes_list.append(category)
                    if not category in categories_routes:
                        categories_routes[category] = []
                    categories_routes[category].append(path)

                    out         = dict_lib.get_nested_dict_from_list(paths)
                    routes_dict = dict_lib.merge_dict(routes_dict,out)

                    if not path in routes_configurations:            routes_configurations[path] = []

                    routes_configurations[path] = {
                        'module':key,
                        'paths':paths,
                        'name':function_name,
                        'arguments':{x:y if x != 'parameters' else [j.__dict__ for j in y] for x,y in fct_n._kwargs.items()}
                    }

    MODULES['routes_list']          = routes_configurations.keys()
    MODULES['routes']               = routes_configurations
    MODULES['routes_paths']         = routes_dict
    MODULES['categories']           = categories_routes_list
    MODULES['categories_routes']    = categories_routes
    return MODULES