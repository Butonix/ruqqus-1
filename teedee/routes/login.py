from flask import *
from teedee.__main__ import app
from teedee.classes.dbModels import *
from teedee.helpers.wrappers import *

#login form
@app.route("/login", methods=["GET"])
@auth_desired
def login_get(v=None):
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

        return redirect("/me")

    else:
        return render_template("login.html", failed=True)

@app.route("/me", methods=["GET"])
@auth_required
def me(v):
    return redirect(v.url)


@app.route("/logout", methods=["POST"])
def logout():

    session.pop("user_id", None)

    return redirect("/")
        
    
