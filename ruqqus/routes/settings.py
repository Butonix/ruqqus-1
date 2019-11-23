from flask import *
from ruqqus.classes import *
from ruqqus.helpers.wrappers import *
from ruqqus.helpers.security import *
from ruqqus.helpers.sanitize import *
from ruqqus.mail import *
from ruqqus.__main__ import db, app

@app.route("/settings/profile", methods=["POST"])
@auth_required
@validate_formkey
def settings_profile_post(v):

    updated=False

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

    if request.form.get("bio") != v.bio:
        updated=True
        bio = request.form.get("bio")
        v.bio=bio

        v.bio_html=sanitize(bio)

    if updated:
        db.add(v)
        db.commit()

        return render_template("settings_profile.html", v=v, msg="Your settings have been saved.")

    else:
        return render_template("settings_profile.html", v=v, error="You didn't change anything.")

@app.route("/settings/security", methods=["POST"])
@auth_required
@validate_formkey
def settings_security_post(v):

    if request.form.get("new_password"):
        if request.form.get("new_password") != request.form.get("cnf_password"):
            return render_template("settings_security.html", v=v, error="Passwords do not match.")

        if not v.verifyPass(request.form.get("old_password")):
            return render_template("settings_security.html", v=v, error="Incorrect password")

        v.passhash=v.hash_password(request.form.get("new_password"))

        db.add(v)
        db.commit()
        
        return render_template("settings_security.html", v=v, msg="Your password has been changed.")

    if request.form.get("new_email"):

        if not v.verifyPass(request.form.get('password')):
            return render_template("settings_security.html", v=v, error="Invalid password")
            
        
        new_email = request.form.get("new_email")
        if new_email == v.email:
            return render_template("settings_security.html", v=v, error="That's already your email!")


        url=f"https://{environ.get('domain')}/activate"
            
        now=int(time.time())

        token=generate_hash(f"{new_email}+{v.id}+{now}")
        params=f"?email={quote(new_email)}&id={v.id}&time={now}&token={token}"

        link=url+params
        
        send_mail(to_address=new_email,
                  subject="Verify your email address.",
                  html=render_template("email/email_change.html",
                                       action_url=link,
                                       v=v)
                  )
        return render_template("settings_security.html", v=v, msg=f"Verify your new email address {new_email} to complete the email change process.")
        

@app.route("/settings/dark_mode/<x>", methods=["POST"])
@auth_required
def settings_dark_mode(x, v):

    try:
        x=int(x)
    except:
        abort(400)

    if x not in [0,1]:
        abort(400)

    if not v.referral_count:
        session["dark_mode_enabled"]=False
        abort(403)
    else:
        session["dark_mode_enabled"]=bool(x)
        return "",204
        
