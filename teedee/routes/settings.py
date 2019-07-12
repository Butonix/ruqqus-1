from flask import *
from teedee.classes import *
from teedee.helpers.wrappers import *
from teedee.__main__ import db, app

@app.route("/settings", methods=["POST"])
@auth_required
@validate_formkey
def settings_post(v):

    updated=False

    if request.form.get("new_password"):
        if request.form.get("new_password") != request.form.get("cnf_password"):
            return render_template("settings.html", v=v, error="Passwords do not match.")

        if not v.confirm_password(request.form.get("old_password")):
            return render_template("settings.html", v=v, error="Incorrect password")

        v.passhash=v.hash_password(request.form.get("new_password"))
        updated=True
                                  

    if request.form.get("over18") != v.over_18:
        updated=True
        v.over_18=bool(request.form.get("over18", None))

    if updated:
        db.add(v)
        db.commit()

        return render_template("settings.html", v=v, msg="Your settings have been saved.")

    else:
        return render_template("settings.html", v=v, error="You didn't change anything.")
