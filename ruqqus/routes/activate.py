from flask import redirect, url_for, flash
from ruqqus.classes.user import *
from ruqqus.__main__ import db


@app.route("/activate", methods=['GET'])
@auth_required
def activate(v):

    hashstr=request.args.get("hashstr", "")

    if not hash:
        return redirect(url_for("index"))

    user = db.query(User).filter(User.activehash == hash).first()

    if not user:

        flash("Invalid activation hash")
        return redirect(url_for("index"))

    elif user.is_activated == True:
        flash("Account is already activated")

    else:
        user.is_activated = True
        db.commit()
        flash("Account has been activated")

    return redirect(url_for("login"))


