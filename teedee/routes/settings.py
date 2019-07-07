from flask import *
from teedee.classes import *
from teedee.helpers.wrappers import *
from teedee.__main__ import db, app

@app.route("/settings", methods=["POST"])
@auth_required
@validate_formkey
def settings_post(v):

    v.over_18=bool(request.form.get("over18", None))

    db.add(v)
    db.commit()

    return render_template("settings.html", msg="Your settings have been saved")
