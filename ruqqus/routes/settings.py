from flask import *
from ruqqus.classes import *
from ruqqus.helpers.wrappers import *
from ruqqus.__main__ import db, app
from ruqqus.mail.mail import send_verification_email

@app.route("/settings", methods=["POST"])
@auth_required
@validate_formkey
def settings_post(v):

    updated=False

    if request.form.get("resend_activation"):
        if not send_verification_email(v):
            return render_template("settings.html", v=v, error="There was an issue sending the E-mail.")
        return render_template("settings.html", v=v, msg="Your Activation E-Mail has been resent")

    if request.form.get("new_password"):
        if request.form.get("new_password") != request.form.get("cnf_password"):
            return render_template("settings.html", v=v, error="Passwords do not match.")

        if not v.verifyPass(request.form.get("old_password")):
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
