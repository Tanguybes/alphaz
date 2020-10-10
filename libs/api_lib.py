from ..models.api import jsonify_data

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