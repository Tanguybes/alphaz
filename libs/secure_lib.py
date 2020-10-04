from bcrypt import hashpw, gensalt, checkpw
import secrets

def secure_password(password):
    password_hashed = hashpw(password.encode(), gensalt())
    return password_hashed

def compare_passwords(password,hash_saved):
    valid = checkpw(str(password).encode(),str(hash_saved).encode())
    return valid

def get_token():
    return secrets.token_urlsafe(45)