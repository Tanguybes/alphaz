from bcrypt import hashpw, gensalt, checkpw
from random import randint
import secrets

def secure_password(password):
    password_hashed = hashpw(password.encode('utf-8'), gensalt())
    try: #todo: remove
        password_hashed = password_hashed.decode('utf-8')
    except:
        pass
    return password_hashed

def compare_passwords(password,hash_saved):
    valid = checkpw(str(password).encode('utf-8'),str(hash_saved).encode('utf-8'))
    return valid

def get_token():
    return secrets.token_urlsafe(45)


def get_keys_numbers(key):
    key_numbers  = [ord(x) for x in key]
    keys_numbers = [x for x in str(sum(key_numbers))[:3]]
    return keys_numbers

def magic_code(key):
    keys_numbers    = get_keys_numbers(key)
    
    values          = [str(randint(100, 999)) + x for x in keys_numbers]
    
    completes       = []
    for value in values[1:]:
        completes.append(''.join([str(9 - int(x)) for x in value]))
    values.extend(completes)
    return '-'.join([str(x) for x in values])
    
def check_magic_code(code,key):
    numbers = code.split('-')
    if len(numbers) != 5: 
        return False
    try:
        numbers = [int(x) for x in numbers]
    except:
        return False
    first = numbers[0]
    summed = sum(numbers)
    operation_valid = first - 2 == int(str(summed)[1:])
    
    keys_numbers = get_keys_numbers(key)
    sequence = [str(numbers[0])[-1], str(numbers[1])[-1], str(numbers[2])[-1]]
    
    return operation_valid and keys_numbers == sequence