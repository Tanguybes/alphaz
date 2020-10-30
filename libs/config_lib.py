import datetime
from collections import OrderedDict

from ..models.database.structure import AlphaDatabase

from core import core

CONSTANTS = {}
PARAMETERS = {}

def order(D: dict) -> OrderedDict:
    return OrderedDict(sorted(values.items(), key=lambda x: len(x[0]),reverse=True))

def get_db_constants(db:AlphaDatabase) -> OrderedDict:
    """Get constants from database

    Args:
        db (AlphaDatabase): [description]

    Returns:
        OrderedDict: constants in a dict with <name> key and <value> value
    """
    model = core.get_table(db,db.name,'constants')

    rows = db.select(model, json=True)
    values = {x['name']:x['value'] for x in rows}

    now                  = datetime.datetime.now()
    values['year']       = now.year
    values['month']      = now.year # TODO: need to update constants each time
    values['day']        = now.year
    values['hour']       = now.year
    values['minute']     = now.year
    values['second']     = now.year

    return order(values)

def get_db_parameters(db:AlphaDatabase) -> OrderedDict:
    """[summary]

    Args:
        db ([type]): [description]
        model ([type]): [description]

    Returns:
        [type]: [description]
    """
    model = core.get_table(db,db.name,'parameters')

    rows = db.select(model, json=True)
    values = {x['name']:x['value'] for x in rows}
    return order(values)

def get_db_constant(db:AlphaDatabase,name:str,update:bool=False):
    """[summary]

    Args:
        db ([type]): [description]
        model ([type]): [description]
        core_ ([type]): [description]
        name ([type]): [description]
        update (bool, optional): [description]. Defaults to False.

    Returns:
        [type]: [description]
    """
    if update:
        get_db_constants(db)

    if not is_db_constant(db,name):
        get_db_constants(db)
        if is_db_constants(db,name):
            return CONSTANTS[name]
        else:
            return None
    return CONSTANTS[name]

def get_db_parameter(db:AlphaDatabase,name:str,update:bool=False):
    """[summary]

    Args:
        db ([type]): [description]
        model ([type]): [description]
        core_ ([type]): [description]
        name ([type]): [description]
        update (bool, optional): [description]. Defaults to False.

    Returns:
        [type]: [description]
    """
    if update:
        get_db_parameters(db)

    if not is_db_parameter(db,name):
        get_db_parameters(db)
        if is_db_parameter(db,name):
            return PARAMETERS[name]
        else:
            return None
    else:
        return PARAMETERS[name]

def set_db_constant(db:AlphaDatabase,name:str,value):
    """[summary]

    Args:
        db ([type]): [description]
        model ([type]): [description]
        name ([type]): [description]
        value ([type]): [description]
    """
    CONSTANTS[name] = value
    model = core.get_table(db,db.name,'constants')
    db.insert_or_update(model,values={'name':name,'value':value})

def set_db_parameter(db:AlphaDatabase,name:str,value): # TODO: set core
    """[summary]

    Args:
        db ([type]): [description]
        model ([type]): [description]
        name ([type]): [description]
        value ([type]): [description]
    """
    PARAMETERS[name] = value
    model = core.get_table(db,db.name,'parameters')
    db.insert_or_update(model,values={'name':name,'value':value})

def is_db_constant(db:AlphaDatabase,name:str):
    """[summary]

    Args:
        core_ ([type]): [description]
        name ([type]): [description]

    Returns:
        [type]: [description]
    """
    return name in CONSTANTS

def is_db_parameter(db:AlphaDatabase,name:str):
    """[summary]

    Args:
        core_ ([type]): [description]
        name ([type]): [description]

    Returns:
        [type]: [description]
    """
    return name in PARAMETERS

def get_api_build(db:AlphaDatabase,update:bool=False):
    """[summary]

    Args:
        db ([type]): [description]
        core_ ([type]): [description]
        update (bool, optional): [description]. Defaults to False.

    Returns:
        [type]: [description]
    """
    build   = get_db_constant(db,'api_build',update=update)
    if build is None:
        build = 0
    return build

def upgrade_api_build(db:AlphaDatabase):
    """[summary]

    Args:
        db ([type]): [description]
        model ([type]): [description]
        core_ ([type]): [description]
    """
    build = get_api_build(db)
    set_db_constant(db,'api_build',int(build) + 1)
