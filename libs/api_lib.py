import sys, os, inspect, copy, requests, enum

from ..libs import dict_lib
from ..utils.api import ROUTES

from ..models.logger import AlphaLogger
from ..models.api import ApiMethods
from ..models.main import AlphaException

from ..libs.json_lib import jsonify_database_models, jsonify_data

MODULES = {}


def get_api_data(
    url: str,
    params: dict = {},
    log: AlphaLogger = None,
    method: ApiMethods = ApiMethods.GET,
    data_only: bool = True,
) -> dict:
    """Get data from api

    Args:
        url (str): [description]
        params (dict, optional): [description]. Defaults to {}.
        log (AlphaLogger, optional): [description]. Defaults to None.
        method (ApiMethods, optional): The request method. Defaults to GET.
        data_only (bool, optional): return only the data. Default to True.

    Returns:
        dict: The request result
    """
    fct = requests.get
    method_str = (
        str(method).lower() if not hasattr(method, "name") else method.name.lower()
    )
    if hasattr(requests, method_str):
        fct = getattr(requests, method_str)

    try:
        resp = fct(url=url, params=params)
    except Exception as ex:
        raise AlphaException(f"Fail to contact {url}", ex=ex)

    if resp.status_code != 200:
        raise AlphaException(f"Fail to get data from {url}: {resp.status_code}")

    try:
        data = resp.json()
    except Exception as ex:
        raise AlphaException(f"Cannot decode answer from {url}", ex=ex)

    if data["error"]:
        raise AlphaException(
            f'Fail to get data from {url}: {data["status"]} - {data["status_description"]}'
        )

    return data["data"] if data_only else data


def get_columns_values_output(objects: list, columns: list = None) -> dict:
    """Get output with columns / values format.

    Args:
        objects (list): [description]
    Args:
        objects (list): [description]
        columns (list): [description]

    Returns:
        dict: [description]
    """
    if len(objects) == 0:
        return {"columns": [], "values": [], "values_nb": 0}

    results = jsonify_data(objects)

    if columns and len(columns) != 0:
        results = [
            {key: value for key, value in result.items() if key in columns}
            for result in results
        ]
    else:
        columns = list(results[0].keys())

    data = {}
    data["columns"] = [x for x in columns if x in results[0]]
    data["values"] = [[x[y] for y in columns if y in x] for x in results]
    data["values_nb"] = len(data["values"])
    return data


def get_routes_infos(
    log: AlphaLogger = None, categories=None, routes=None, reload_=False
) -> dict:
    """Get all apis routes with informations.

    Args:
        log ([AlphaLogger], optional): [description]. Defaults to None.
    Args:
        log ([AlphaLogger], optional): [description]. Defaults to None.

    Returns:
        dict: [description]
    """
    global ROUTES
    if len(MODULES) != 0 and not reload_:
        return MODULES

    if log:
        log.debug(
            f"Getting {'alphaz' if not all else 'all'} routes from loaded modules"
        )

    routes_dict = {}

    for path, cg in ROUTES.items():
        out = dict_lib.get_nested_dict_from_list(cg["paths"])
        routes_dict = dict_lib.merge_dict(routes_dict, out)
    categories = list(set([x["category"] for x in ROUTES.values()]))
    categories.sort()

    routes_dict = dict_lib.sort_dict(routes_dict)

    MODULES["routes_list"] = ROUTES.keys()
    MODULES["routes"] = ROUTES
    MODULES["routes_paths"] = routes_dict
    MODULES["categories"] = categories
    MODULES["categories_routes"] = {
        c: [x for x, y in ROUTES.items() if y["category"] == c] for c in categories
    }
    return MODULES
