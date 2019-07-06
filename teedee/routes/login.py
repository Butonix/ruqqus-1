from flask import *
from teedee.classes import *
from teedee.helpers.wrappers import *
from teedee.helpers.base36 import *
from secrets import token_hex
from time import time
import hmac
from os import environ
import re

from teedee.__main__ import app

valid_username_regex=re.compile("^\w{5,}$")
valid_password_regex=re.compile("^.{8,}$")

#login form
@app.route("/login", methods=["GET"])
@auth_desired
def login_get(v):
    if v:
        return redirect("/")

    return render_template("login.html", failed=False)

#login post procedure
@app.route("/login", methods=["POST"])
def login_post():

    username=request.form.get("username")

    #step1: identify if username is username or email
    if "@" in username:
        try:
            account = db.query(User).filter_by(email=username).first()
        except IndexError:
            return render_template("login.html", failed=True)

    else:
        try:
            account = db.query(User).filter_by(username=username).first()
        except IndexError:
            return render_template("login.html", failed=True)

    #test password
    if account.verifyPass(request.form.get("password")):

        #set session user id
        session["user_id"]=account.id
        session["session_id"]=token_hex(16)

        return redirect("/me")

    else:
        return render_template("login.html", failed=True)

@app.route("/me", methods=["GET"])
@auth_required
def me(v):
    return redirect(v.url)


@app.route("/logout", methods=["POST"])
@auth_required
@validate_formkey
def logout(v):

    session.pop("user_id", None)
    session.pop("session_id", None)

    return redirect("/")

#signing up
@app.route("/signup", methods=["GET"])
@auth_desired
def sign_up_get(v):
    if v:
        return redirect("/")
    
    agent=request.headers.get("User-Agent", None)
    if not agent:
        abort(403)
    
    #Make a unique form key valid for one account creation
    now = int(time())
    token = token_hex(16)
    session["signup_token"]=token
    ip=request.remote_addr
    
    formkey_hashstr = str(now)+token+ip+agent

    
    #formkey is a hash of session token, timestamp, and IP address
    formkey = hmac.new(key=bytes(environ.get("MASTER_KEY"), "utf-16"),
                   msg=bytes(formkey_hashstr, "utf-16")
                  ).hexdigest()
    
    return render_template("sign_up.html", formkey=formkey, now=now)

#signup api
@app.route("/signup", methods=["POST"])
@auth_desired
def sign_up_post(v):
    if v:
        abort(403)
        
    agent=request.headers.get("User-Agent", None)
    if not agent:
        abort(403)
    
    form_timestamp = request.form.get("now", 0)
    form_formkey = request.form.get("formkey","none")
    
    submitted_token=session["signup_token"]
    ip=request.remote_addr
    
    correct_formkey_hashstr = str(form_timestamp)+submitted_token+ip+agent
    
    correct_formkey = hmac.new(key=bytes(environ.get("MASTER_KEY"), "utf-16"),
                   msg=bytes(correct_formkey_hashstr, "utf-16")
                  ).hexdigest()
    
    now=int(time())

    #debugging stuff - remove once done
    print(f"submitted formkey: {form_formkey}")
    print(f"correct formkey: {correct_formkey}")
    print(f"form timestamp: {form_timestamp}")
    print(f"now: {time()}")
    

    #define function that takes an error message and generates a new signup form
    def new_signup(error):
        
        #Reset tokens and return to signup form
        
        token = token_hex(16)
        session["signup_token"]=token

        new_formkey_hashstr=str(now)+submitted_token+ip+agent
        new_formkey = hmac.new(key=bytes(environ.get("MASTER_KEY"), "utf-16"),
                               msg=bytes(new_formkey_hashstr, "utf-16")
                               ).hexdigest()
        
        return render_template("sign_up.html", formkey=new_formkey, now=now, error=error)

    #check for tokens
    if (now-int(form_timestamp)>120
        or not hmac.compare_digest(form_formkey, correct_formkey)
       ):
        return new_signup("There was a problem. Please try again.")

    #check for matched passwords
    if not request.form.get("password") == request.form.get("password_confirm"):
        return new_signup("Password and Confirm Password do not match.")

    #check username/pass conditions
    if not re.match(valid_username_regex, request.form.get("username")):
        return new_signup("Invalid username")

    if not re.match(valid_password_regex, request.form.get("password")):
        return new_signup("Password must be 8 characters or longer")

    #Check for existing acocunts
    if (db.query(User).filter_by(email=request.form.get("email")).first()
        or db.query(User).filter_by(username=request.form.get("username")).first()):
        return new_signup("An account with that username or email already exists.")
    
    #success
    
    #kill tokens
    session.pop("signup_token")
    
    session["session_id"]=token_hex(16)
    
    #make new user
    try:
        new_user=User(username=request.form.get("username"),
                  password=request.form.get("password"),
                  email=request.form.get("email"),
                  created_utc=int(time())
                 )
    except:
        return new_signup("Please enter a valid email")
    
    db.add(new_user)
    db.commit()
    
    v=db.query(User).filter_by(username=request.form.get("username")).first()
    return redirect(v.url)
    
