from flask import *
from teedee.classes import *
from teedee.helpers.wrappers import *
from teedee.helpers.base36 import *
from secrets import token_hex
from teedee.__main__ import app

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
@validate_form
def logout(v):

    session.pop("user_id", None)
    session.pop("session_id", None)

    return redirect("/")

@app.route("/make-session-id")
def make_id(v):

    session["session_id"]=token_hex(16)

    return redirect("/")
    
