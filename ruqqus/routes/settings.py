from flask import *
from sqlalchemy import func
import time
import threading
from ruqqus.classes import *
from ruqqus.helpers.wrappers import *
from ruqqus.helpers.security import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.aws import check_csam_url
from ruqqus.mail import *
from ruqqus.__main__ import db, app, cache

@app.route("/settings/profile", methods=["POST"])
@is_not_banned
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
        cache.delete_memoized(User.idlist, v)

    if request.form.get("hide_offensive") != v.hide_offensive:
        updated=True
        v.hide_offensive=bool(request.form.get("hide_offensive", None))
        cache.delete_memoized(User.idlist, v)
        
    if request.form.get("private") != v.is_private:
        updated=True
        v.is_private=bool(request.form.get("private", None))
        
    if request.form.get("bio") != v.bio:
        updated=True
        bio = request.form.get("bio")[0:256]
        v.bio=bio

        v.bio_html=sanitize(bio)


    x=int(request.form.get("title_id",0))
    if x==0:
        v.title_id=None
        updated=True
    elif x>0:
        title =get_title(x)
        if bool(eval(title.qualification_expr)):
            v.title_id=title.id
            updated=True
        else:
            return render_template("settings_profile.html",
                                   v=v,
                                   error=f"Unable to set title {title.text} - {title.requirement_string}"
                                   )
    else:
        abort(400)
        
    if updated:
        db.add(v)
        db.commit()

        return render_template("settings_profile.html",
                               v=v,
                               msg="Your settings have been saved."
                               )

    else:
        return render_template("settings_profile.html",
                               v=v,
                               error="You didn't change anything."
                               )

@app.route("/settings/security", methods=["POST"])
@is_not_banned
@validate_formkey
def settings_security_post(v):

    if request.form.get("new_password"):
        if request.form.get("new_password") != request.form.get("cnf_password"):
            return redirect("/settings/security?error="+escape("Passwords do not match."))

        if not v.verifyPass(request.form.get("old_password")):
            return render_template("settings_security.html", v=v, error="Incorrect password")

        v.passhash=v.hash_password(request.form.get("new_password"))

        db.add(v)
        db.commit()
        
        return redirect("/settings/security?msg="+escape("Your password has been changed."))

    if request.form.get("new_email"):

        if not v.verifyPass(request.form.get('password')):
            return redirect("/settings/security?error="+escape("Invalid password."))
            
        
        new_email = request.form.get("new_email")
        if new_email == v.email:
            return redirect("/settings/security?error="+escape("That's already your email."))

        #check to see if email is in use
        existing=db.query(User).filter(User.id != v.id,
                                       func.lower(User.email) == new_email.lower()).first()
        if existing:
            return redirect("/settings/security?error="+escape("That email address is already in use."))

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
        
        return redirect("/settings/security?msg="+escape("Check your email and click the verification link to complete the email change."))
    
    if request.form.get("2fa_token", ""):
        
        if not v.verifyPass(request.form.get('password')):
            return redirect("/settings/security?error="+escape("Invalid password or token."))
            
        secret=request.form.get("2fa_secret")
        x=pyotp.TOTP(secret)
        if not x.verify(request.form.get("2fa_token"), valid_window=1):
            return redirect("/settings/security?error="+escape("Invalid password or token."))
    
        v.mfa_secret=secret
        db.add(v)
        db.commit()
    
        return redirect("/settings/security?msg="+escape("Two-factor authentication enabled."))
    
    if request.form.get("2fa_remove",""):
        
        if not v.verifyPass(request.form.get('password')):
            return redirect("/settings/security?error="+escape("Invalid password or token."))
            
        token=request.form.get("2fa_remove")
        
        if not v.validate_2fa(token):
            return redirect("/settings/security?error="+escape("Invalid password or token."))
        
        v.mfa_secret=None
        db.add(v)
        db.commit()
        return redirect("/settings/security?msg="+escape("Two-factor authentication disabled."))
            


@app.route("/settings/dark_mode/<x>", methods=["POST"])
@auth_required
@validate_formkey
def settings_dark_mode(x, v):

    try:
        x=int(x)
    except:
        abort(400)

    if x not in [0,1]:
        abort(400)

    if not v.can_use_darkmode:
        session["dark_mode_enabled"]=False
        abort(403)
    else:
        #print(f"current cookie is {session.get('dark_mode_enabled')}")
        session["dark_mode_enabled"]=x
        #print(f"set dark mode @{v.username} to {x}")
        #print(f"cookie is now {session.get('dark_mode_enabled')}")
        session.modified=True
        return "",204
        
@app.route("/settings/log_out_all_others", methods=["POST"])
@auth_required
@validate_formkey
def settings_log_out_others(v):

    submitted_password=request.form.get("password","")

    if not v.verifyPass(submitted_password):
        return render_template("settings_security.html", v=v, error="Incorrect Password"), 401

    #increment account's nonce
    v.login_nonce +=1

    #update cookie accordingly
    session["login_nonce"]=v.login_nonce

    db.add(v)
    db.commit()

    return render_template("settings_security.html", v=v, msg="All other devices have been logged out")



@app.route("/settings/images/profile", methods=["POST"])
@auth_required
@validate_formkey
def settings_images_profile(v):

    v.set_profile(request.files["profile"])

    #anti csam
    new_thread=threading.Thread(target=check_csam_url,
                                args=(v.profile_url,
                                      v,
                                      lambda:board.del_profile()
                                      )
                                )
    new_thread.start()

    return render_template("settings_profile.html", v=v, msg="Profile picture successfully updated.")

@app.route("/settings/images/banner", methods=["POST"])
@auth_required
@validate_formkey
def settings_images_banner(v):

    v.set_banner(request.files["banner"])

    #anti csam
    new_thread=threading.Thread(target=check_csam_url,
                                args=(v.banner,
                                      v,
                                      lambda:board.del_banner()
                                      )
                                )
    new_thread.start()

    return render_template("settings_profile.html", v=v, msg="Banner successfully updated.")


@app.route("/settings/delete/profile", methods=["POST"])
@auth_required
@validate_formkey
def settings_delete_profile(v):

    v.del_profile()

    return render_template("settings_profile.html", v=v, msg="Profile picture successfully removed.")

@app.route("/settings/delete/banner", methods=["POST"])
@auth_required
@validate_formkey
def settings_delete_banner(v):

    v.del_banner()

    return render_template("settings_profile.html", v=v, msg="Banner successfully removed.")



@app.route("/settings/toggle_collapse", methods=["POST"])
@auth_required
@validate_formkey
def settings_toggle_collapse(v):

    session["sidebar_collapsed"]=not session.get("sidebar_collapsed",False)

    return "", 204



@app.route("/settings/read_announcement", methods=["POST"])
@auth_required
@validate_formkey
def update_announcement(v):

    v.read_announcement_utc=int(time.time())
    db.add(v)
    db.commit()
    return "", 204
