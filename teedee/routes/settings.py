from flask import *
from teedee.classes import *
from teedee.helpers.wrappers import *
from teedee.__main__ import db, app

@app.route("/api/settings", methods=["POST"])
@auth_required
@validate_formkey
def settings_post(v):

    v.over_18=request.form.get("over18", False)

    db.add(v)
    db.commit()
