import sys, os, inspect, copy

def get_routes_infos(all=False):
    modules = {}

    imported_modules = copy.copy(sys.modules)
    for key, module in imported_modules.items():
        if 'alphaz' in key or os.getcwd().split(os.sep)[-1] in str(module) or all:
            try:
                functions_list  = [o for o in inspect.getmembers(module) if inspect.isfunction(o[1])]
            except:
                continue

            for function_tuple in functions_list:
                function_name, fct = function_tuple

                fct_n = getattr(module,function_name)
                wraps = inspect.unwrap(fct)

                if 'route.' in str(wraps):
                    if not key in modules:            modules[key] = []
                    #print(function_name,wraps,wraps.__name__,inspect.signature(fct,follow_wrapped=False),inspect.signature(wraps),inspect.unwrap(wraps))
                    modules[key].append({'name':function_name,'arguments':{x:y if x != 'parameters' else [j.__dict__ for j in y] for x,y in fct_n._kwargs.items()}})
    return modules