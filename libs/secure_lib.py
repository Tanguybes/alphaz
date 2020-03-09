from bcrypt import hashpw, gensalt
import secrets

def secure_password(password):
    password_hashed = hashpw(password.encode(), gensalt())
    return password_hashed

def compare_passwords(password,hash_saved):
    hash_compare    = hashpw(password.encode(), hash_saved.encode())
    return hash_compare == hash_saved.encode()

def get_token():
    return secrets.token_urlsafe(45)