from flask import *
from time import time
import hmac
from os import environ
import re

from ruqqus.classes import *
from ruqqus.helpers.wrappers import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.security import *
from ruqqus.mail import send_verification_email
from secrets import token_hex


from ruqqus.mail import *
from ruqqus.__main__ import app

valid_username_regex=re.compile("^\w{5,}$")
valid_password_regex=re.compile("^.{8,}$")

#login form
@app.route("/login", methods=["GET"])
@auth_desired
def login_get(v):
    if v:
        return redirect("/")

    random_image()

    return render_template("login.html",
                           failed=False,
                           i=random_image())

#login post procedure
@app.route("/login", methods=["POST"])
def login_post():

    username=request.form.get("username")

    #step1: identify if username is username or email
    if "@" in username:
        account = db.query(User).filter_by(email=username).first()
        if not account:
            return render_template("login.html", failed=True, i=random_image())

    else:
        account = db.query(User).filter_by(username=username).first()
        if not account:
            return render_template("login.html", failed=True, i=random_image())

    #test password
    if account.verifyPass(request.form.get("password")):

        #set session user id
        session["user_id"]=account.id
        session["session_id"]=token_hex(16)

        return redirect(account.url)

    else:
        return render_template("login.html", failed=True, i=random_image())

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

    #get a random image
    image = random_image()

    
    #formkey is a hash of session token, timestamp, and IP address
    formkey = hmac.new(key=bytes(environ.get("MASTER_KEY"), "utf-16"),
                       msg=bytes(formkey_hashstr, "utf-16")
                       ).hexdigest()
    
    return render_template("sign_up.html",
                           formkey=formkey,
                           now=now,
                           i=image
                           )

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
    
    correct_formkey_hashstr = form_timestamp+submitted_token+ip+agent
    
    correct_formkey = hmac.new(key=bytes(environ.get("MASTER_KEY"), "utf-16"),
                               msg=bytes(correct_formkey_hashstr, "utf-16")
                               ).hexdigest()
    
    now=int(time())
    

    #define function that takes an error message and generates a new signup form
    def new_signup(error):
        
        #Reset tokens and return to signup form
        
        token = token_hex(16)
        session["signup_token"]=token
        now=int(time())
        agent=request.headers.get("User-Agent", None)
        ip=request.remote_addr

        new_formkey_hashstr=str(now)+submitted_token+ip+agent
        new_formkey = hmac.new(key=bytes(environ.get("MASTER_KEY"), "utf-16"),
                               msg=bytes(new_formkey_hashstr, "utf-16")
                               ).hexdigest()
        
        return render_template("sign_up.html", formkey=new_formkey, now=now, error=error, i=random_image())

    #check for tokens
    if now-int(form_timestamp)>120:
        print("form expired")
        return new_signup("There was a problem. Please refresh the page and try again.")
    elif now-int(form_timestamp)<5:
        print("slow down!")
        return new_signup("There was a problem. Please refresh the page and try again.")

    if not hmac.compare_digest(correct_formkey, form_formkey):
        print(f"{request.form.get('username')} - mismatched formkeys")
        return new_signup("There was a problem. Please refresh the page and try again.")

    #check for matched passwords
    if not request.form.get("password") == request.form.get("password_confirm"):
        return new_signup("Password and Confirm Password do not match.")

    #check username/pass conditions
    if not re.match(valid_username_regex, request.form.get("username")):
        return new_signup("Invalid username")

    if not re.match(valid_password_regex, request.form.get("password")):
        return new_signup("Password must be 8 characters or longer")

    #Check for existing acocunts

    if (db.query(User).filter(User.username.ilike(request.form.get("username"))).first()
        or db.query(User).filter(User.email.ilike(request.form.get("email"))).first()):
        return new_signup("An account with that username or email already exists.")       
    
    #success
    
    #kill tokens
    session.pop("signup_token")
    
    #make new user
    try:
        new_user=User(username=request.form.get("username"),
                      password=request.form.get("password"),
                      email=request.form.get("email"),
                      created_utc=int(time()),
                      creation_ip=request.remote_addr
                 )

    except Exception as e:
        print(e)
        return new_signup("Please enter a valid email")
    
    db.add(new_user)
    db.commit()

    send_verification_email(new_user)

    session["user_id"]=new_user.id
    session["session_id"]=token_hex(16)
    
    return redirect(new_user.permalink)
    
