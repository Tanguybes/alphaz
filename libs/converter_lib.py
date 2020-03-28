'''
Created on 13 janv. 2019

@author: aurele durand
'''

def to_int(value):
    try:
        return int(value), True
    except ValueError:
        return value, False
    
def to_num(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s
        
def is_num(s):
    if s is None:
        return False
    try:
        a = int(s)
        return True
    except ValueError:
        try:
            a = float(s)
            return True
        except ValueError:
            return False

def is_int(val):
    try:
        num = int(val)
    except ValueError:
        return False
    return True
        
def format_as_string_if_not_num(s):
    s = "'%s'"%s if not is_num(s) else s
    return s