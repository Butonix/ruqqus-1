from flask import redirect, url_for, flash, request, abort
from ruqqus.classes.user import *
from ruqqus.__main__ import db
from ruqqus.helpers.security import *

@app.route("/activate", methods=['GET'])
def activate():


    token=request.args.get("token", "")
    email=request.args.get("email", "")
    id=request.args.get("id", "")
    time=request.args.get("time", "")


    user = db.query(User).filter(User.id == id).first()

    if not user:
        flash("User Does Not Exist")
        return redirect(url_for("index"))

    if user.is_activated == True:
        flash("Account is already activated")
        return redirect(url_for("login"))

    check_hash = validate_hash(f"{email}+{id}+{time}", token)

    if not check_hash:
        flash("Invalid Token")
        return redirect(url_for("index"))

    if user.is_activated == False:
        user.is_activated = True
        db.add(user)
        db.commit()
        flash("Account has been activated")
        return redirect(url_for("login"))




