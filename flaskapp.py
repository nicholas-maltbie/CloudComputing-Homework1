from flask import Flask, render_template, request, redirect, session, url_for, Response
from flask_mysqldb import MySQL

import os
import re
import boto3
import password_utils
import user_manager

app = Flask(__name__)

# Load configuration from config file
app.config.from_object('config.Default')


def get_s3_client():
    return boto3.client('s3',
        region_name = app.config["S3_REGION"],
        aws_access_key_id = app.config["S3_KEY"],
        aws_secret_access_key = app.config["S3_SECRET"])
def get_s3_resource():
    return boto3.resource('s3',
        region_name = app.config["S3_REGION"],
        aws_access_key_id = app.config["S3_KEY"],
        aws_secret_access_key = app.config["S3_SECRET"])
    
BUCKET = "homework1-nickmaltbie"

mysql = MySQL(app)

@app.route("/upload", methods=['POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('index'))
    if request.files['myfile'].filename == "":
        return redirect(url_for('account'))

    data = request.files['myfile'].read()
    words = data.split()
    request.files['myfile'].seek(0)
    
    s3 = get_s3_resource()
    cur = mysql.connection.cursor()
    user_manager.update_or_add(session['username'], request.files['myfile'].filename, len(words), cur)
    mysql.connection.commit()
    cur.close()
    
    s3.Bucket(BUCKET).put_object(Key=session['username'], Body=request.files['myfile'])
    return redirect(url_for('account'))

@app.route("/download", methods=['GET'])
def download():
    if 'username' not in session:
        return redirect(url_for('index'))
    cur = mysql.connection.cursor()
    fileName, fileWords = user_manager.get_user_file_details(session['username'], cur)
    cur.close()
    print("Found file name of: ", fileName)
    if fileName == None or fileName == "":
        return Response(status = 204)

    s3 = get_s3_client()

    f = s3.get_object(Bucket=BUCKET, Key=session['username'])

    return Response(
        f['Body'].read(),
        mimetype='text/plain/',
        headers={"Content-Disposition": "attachment;filename=" + fileName}
    )

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' in session:
        return render_template('index-login.html')
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('account'))
    if request.method == "POST":
        error = None
        details = request.form
        username = details['username']
        password = details['password']

        if len(username) < 8:
            error = "Username must be at least 8 characters long"
        if len(username) > 32:
            error = "Username must be less than 32 characters long"
        if re.fullmatch(user_manager.valid_username_regex, username) is None:
            error = "Username can only contain A-Z a-z 0-9 -_."

        cur = mysql.connection.cursor()
        error = password_utils.check_user_password(username, password, cur)
        cur.close()

        if error:
            return render_template(
                    'login.html',
                    error=error,
                    username=username)
        session['username'] = username
        return redirect(url_for('account'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/account', methods=['GET', 'POST'])
def account():
    if 'username' not in session:
        return redirect(url_for('index'))

    cur = mysql.connection.cursor()
    details = user_manager.get_user_info(session['username'], cur)
    fileName, fileWords = user_manager.get_user_file_details(session['username'], cur)
    cur.close()
    return render_template(
        'account.html',
        username=session['username'],
        email=details['email'] if 'email' in details else 'ERROR: EMAIL NOT FOUND',
        firstName=details['firstName'] if 'firstName' in details else 'ERROR: FIRST NAME NOT FOUND',
        lastName=details['lastName'] if 'lastName' in details else 'ERROR: LAST NAME NOT FOUND',
        myfile=fileName if fileName != None else 'No file uploaded yet',
        fileWords=str(fileWords) if fileWords != None else 'N/A'

    )
        

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session:
        return redirect(url_for('account'))
    if request.method == "POST":
        error = None

        details = request.form
        username = details['username']
        email = details['email']
        password = details['password']
        password2 = details['password2']
        firstName = details['fname']
        lastName = details['lname']

        error = user_manager.is_info_valid(username, email, firstName, lastName)
        if not error:
            error = password_utils.is_valid_password(password)
        if not error:
            cur = mysql.connection.cursor()
            error = user_manager.is_username_taken(username, cur)
            cur.close()
        if not error and password2 != password:
            error = "Passwords must match"

        if error:
            return render_template(
                    'register.html',
                    username=username,
                    error=error,
                    password=password,
                    password2=password2,
                    fname=firstName,
                    lname=lastName,
                    email=email)

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO MyUsers(username, email, firstname, lastname) VALUES (%s, %s, %s, %s)",
                (username, email, firstName, lastName))
        password_error = password_utils.add_user_password(username, password, cur)
        mysql.connection.commit()
        cur.close()
        session['username'] = username
        return redirect(url_for('account'))
    return render_template('register.html')

if __name__ == '__main__':
    app.run()


