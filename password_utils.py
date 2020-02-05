import hashlib
import re
import os

default_hash = 'sha256'
default_iter = 1000
default_salt_size = 16

def get_password_hash(hash_name, plaintext, salt, iterations):
    current = plaintext
    return hashlib.pbkdf2_hmac(hash_name, plaintext.encode(), bytes.fromhex(salt), iterations).hex()

def get_random_salt(size):
    return os.urandom(size).hex()

def user_has_password(username, cur):
    cur.execute("SELECT * FROM Passwords WHERE username=%s", (username,))
    return cur.rowcount > 0

def add_user_password(username, plaintext_password, cur):
    if user_has_password(username, cur):
        return "User already has password"
    salt = get_random_salt(default_salt_size)
    iterations = default_iter
    password_hash = get_password_hash(default_hash, plaintext_password, salt, iterations)

    args = [username, password_hash, salt, iterations]
    cur.execute("INSERT INTO Passwords(username, passwordHash, salt, iterations) VALUES (%s, %s, %s, %s)", args)
    return None

def is_valid_password(password):
    if (len(password) < 8):
        return "Password must be at least 8 characters long"
    if (len(password) > 32):
        return "Password cannot be longer than 32 characters"
    elif not re.search("[A-Za-z]", password):
        return "Password must contain at least one letter [A-Z] or [a-z]"
    elif not re.search("[0-9]", password):
        return "Password must contain at least one number"
    elif not re.search("[@_!#$%^&*()<>?/\|}{~:-]", password):
        return "Password must contain one special character from '@_!#$%^&*()<>?/\|}{~:'"
    elif re.search("/s", password):
        return "Password cannot contain spaces"
    return None

def check_user_password(username, plaintext_password, cur):
    if not user_has_password(username, cur):
        return "Incorrect username or password"
    select = ['passwordHash', 'salt', 'iterations']
    cur.execute("SELECT passwordHash, salt, iterations FROM Passwords WHERE username=%s",(username,))
    row = cur.fetchone()
    row_dict = dict()
    for key, val in zip(select, row):
        row_dict[key] = val
    salt = row_dict['salt']
    iterations = row_dict['iterations']
    true_hash = row_dict['passwordHash']

    input_hash = get_password_hash(default_hash, plaintext_password, salt, iterations)

    print(input_hash, true_hash, input_hash == true_hash)

    if input_hash == true_hash:
        return None

    return "Incorrect username or password"

