from flask import *
from teedee.classes import *
from teedee.helpers.wrappers import *
from teedee.__main__ import db, app

@app.route("/settings", methods=["POST"])
@auth_required
@validate_formkey
def settings_post(v):

    v.over_18=request.form.get("over18")

    db.add(v)
    db.commit()

    return render_template("settings.html", msg="Your settings have been saved")
