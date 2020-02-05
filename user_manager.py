import re

email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
valid_name_regex = "[A-Za-z0-9]+"
valid_username_regex = "[A-Za-z0-9\s@._-]+"

def is_username_taken(username, cur):
    cur.execute("SELECT username FROM MyUsers WHERE username=%s", [username])

    error = None
    if cur.rowcount > 0:
        error = "Account with that username already exists"
    return error

def is_info_valid(username, email, fname, lname):
    if len(username) < 8:
        return "Username must be at least 8 characters long"
    if len(username) > 32:
        return "Username must be less than 32 characters long"
    if re.fullmatch(valid_username_regex, username) is None:
        return "Username can only contain A-Z a-z 0-9"
    if not re.search(email_regex, email):
        return "invalid email address"
    if len(email) > 255:
        return "Email must be less than 255 characters long"
    if len(fname) == 0:
        return "First name cannot be empty"
    if len(lname) == 0:
        return "Last name cannot be empty"
    if len(fname) > 32:
        return "First name must be less than 32 characters long"
    if len(lname) > 32:
        return "First name must be less than 32 characters long"
    if re.fullmatch(valid_name_regex, fname) is None:
        return "First name can only contain [A-Za-z]"
    if re.fullmatch(valid_name_regex, lname) is None:
        return "last name can only contain [A-Za-z]"
    return None

def get_user_info(username, cur):
    if not is_username_taken(username, cur):
        return None
    
    select = ['email', 'firstName', 'lastName']
    cur.execute("SELECT email, firstName, lastName FROM MyUsers WHERE username=%s", [username])
    row = cur.fetchone()
    row_dict = dict()
    for key, val in zip(select, row):
        row_dict[key] = val
    return row_dict

    


