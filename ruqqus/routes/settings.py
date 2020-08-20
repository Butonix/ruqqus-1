from flask import *
from sqlalchemy import func
import time
import threading
import mistletoe
from ruqqus.classes import *
from ruqqus.helpers.wrappers import *
from ruqqus.helpers.security import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.markdown import *
from ruqqus.helpers.aws import check_csam_url
from ruqqus.mail import *
from .front import frontlist
from ruqqus.__main__ import app, cache

@app.route("/settings/profile", methods=["POST"])
@is_not_banned
@validate_formkey
def settings_profile_post(v):

    updated=False                             

    if request.values.get("over18", v.over_18) != v.over_18:
        updated=True
        v.over_18=request.values.get("over18", None)=='true'
        cache.delete_memoized(User.idlist, v)

    if request.values.get("hide_offensive", v.hide_offensive) != v.hide_offensive:
        updated=True
        v.hide_offensive=request.values.get("hide_offensive", None)=='true'
        cache.delete_memoized(User.idlist, v)

    if request.values.get("show_nsfl", v.show_nsfl) != v.show_nsfl:
        updated=True
        v.show_nsfl=request.values.get("show_nsfl", None)=='true'
        cache.delete_memoized(User.idlist, v)

    if request.values.get("filter_nsfw", v.filter_nsfw) != v.filter_nsfw:
        updated=True
        v.filter_nsfw= not request.values.get("filter_nsfw", None)=='true'
        cache.delete_memoized(User.idlist, v)
        
    if request.values.get("private", v.is_private) != v.is_private:
        updated=True
        v.is_private=request.values.get("private", None)=='true'
        
    if request.values.get("bio") is not None:
        bio = request.values.get("bio")[0:256]

        if bio==v.bio:
            return render_template("settings_profile.html",
                v=v,
                error="You didn't change anything")

        v.bio=bio

        with CustomRenderer() as renderer:
            v.bio_html=renderer.render(mistletoe.Document(bio))
        v.bio_html=sanitize(v.bio_html, linkgen=True)
        g.db.add(v)
        return render_template("settings_profile.html",
            v=v,
            msg="Your bio has been updated.")


    x=request.values.get("title_id",None)
    if x:
        x=int(x)
        if x==0:
            v.title_id=None
            updated=True
        elif x>0:
            title =get_title(x)
            if bool(eval(title.qualification_expr)):
                v.title_id=title.id
                updated=True
            else:
                return jsonify({"error":f"You don't meet the requirements for title `{title.text}`."}), 403
        else:
            abort(400)
        
    if updated:
        g.db.add(v)
        

        return jsonify({"message":"Your settings have been updated."})

    else:
        return jsonify({"error":"You didn't change anything."}), 400

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

        g.db.add(v)
        
        
        return redirect("/settings/security?msg="+escape("Your password has been changed."))

    if request.form.get("new_email"):

        if not v.verifyPass(request.form.get('password')):
            return redirect("/settings/security?error="+escape("Invalid password."))
            
        
        new_email = request.form.get("new_email")
        if new_email == v.email:
            return redirect("/settings/security?error="+escape("That email is already yours!"))

        #check to see if email is in use
        existing=g.db.query(User).filter(User.id != v.id,
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
        g.db.add(v)
        
    
        return redirect("/settings/security?msg="+escape("Two-factor authentication enabled."))
    
    if request.form.get("2fa_remove",""):
        
        if not v.verifyPass(request.form.get('password')):
            return redirect("/settings/security?error="+escape("Invalid password or token."))
            
        token=request.form.get("2fa_remove")
        
        if not v.validate_2fa(token):
            return redirect("/settings/security?error="+escape("Invalid password or token."))
        
        v.mfa_secret=None
        g.db.add(v)
        
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

    g.db.add(v)
    

    return render_template("settings_security.html", v=v, msg="All other devices have been logged out")



@app.route("/settings/images/profile", methods=["POST"])
@auth_required
@validate_formkey
def settings_images_profile(v):
    if v.can_upload_avatar:
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

    return render_template("settings_profile.html", v=v, msg="Avatars require 300 reputation.")

@app.route("/settings/images/banner", methods=["POST"])
@auth_required
@validate_formkey
def settings_images_banner(v):
    if v.can_upload_banner:
        v.set_banner(request.files["banner"])

        #anti csam
        new_thread=threading.Thread(target=check_csam_url,
                                    args=(v.banner_url,
                                          v,
                                          lambda:board.del_banner()
                                          )
                                    )
        new_thread.start()

        return render_template("settings_profile.html", v=v, msg="Banner successfully updated.")

    return render_template("settings_profile.html", v=v, msg="Banners require 500 reputation.")


@app.route("/settings/delete/profile", methods=["POST"])
@auth_required
@validate_formkey
def settings_delete_profile(v):

    v.del_profile()

    return render_template("settings_profile.html", v=v, msg="Profile picture successfully removed.")

@app.route("/settings/new_feedkey", methods=["POST"])
@auth_required
@validate_formkey
def settings_new_feedkey(v):

    v.feed_nonce+=1
    g.db.add(v)
    

    return render_template("settings_profile.html", v=v, msg="Your new custom RSS Feed Token has been generated.")

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
    g.db.add(v)
    
    return "", 204


@app.route("/settings/delete_account", methods=["POST"])
@is_not_banned
@validate_formkey
def delete_account(v):

    if not v.verifyPass(request.form.get("password","")) or (v.mfa_secret and not v.validate_2fa(request.form.get("twofactor",""))):
        return render_template("settings_security.html", v=v, error="Invalid password or token" if v.mfa_secret else "Invalid password")

    v.is_deleted=True
    v.login_nonce+=1
    v.delete_reason=request.form.get("delete_reason","")
    v.del_banner()
    v.del_profile()
    g.db.add(v)

    mods=g.db.query(ModRelationship).filter_by(user_id=v.id).all()
    for mod in mods:
        g.db.delete(mod)

    bans=g.db.query(BanRelationship).filter_by(user_id=v.id).all()
    for ban in bans:
        g.db.delete(ban)

    contribs=g.db.query(ContributorRelationship).filter_by(user_id=v.id).all()
    for contrib in contribs:
        g.db.delete(contrib)

    blocks=g.db.query(UserBlock).filter_by(target_id=v.id).all()
    for block in blocks:
        g.db.delete(block)
    

    session.pop("user_id", None)
    session.pop("session_id", None)

    return redirect('/')


@app.route("/settings/blocks", methods=["GET"])
@auth_required
def settings_blockedpage(v):

    #users=[x.target for x in v.blocked]

    return render_template("settings_blocks.html",
        v=v)

@app.route("/settings/filters", methods=["GET"])
@auth_required
def settings_blockedguilds(v):

    #users=[x.target for x in v.blocked]

    return render_template("settings_guildfilter.html",
        v=v)

@app.route("/settings/block", methods=["POST"])
@auth_required
@validate_formkey
def settings_block_user(v):

    user=get_user(request.values.get("username"), graceful=True)

    if not user:
        return jsonify({"error":"That user doesn't exist."}), 404

    if user.id==v.id:
        return jsonify({"error":"You can't block yourself."}), 409

    if v.has_block(user):
        return jsonify({"error":f"You have already blocked @{user.username}."}), 409

    if user.id==1:
        return jsonify({"error":"You can't block @ruqqus."}), 409


    new_block=UserBlock(user_id=v.id,
                        target_id=user.id,
                        created_utc=int(time.time())
                        )
    g.db.add(new_block)

    cache.delete_memoized(v.idlist)
    #cache.delete_memoized(Board.idlist, v=v)
    cache.delete_memoized(frontlist, v=v)

    return jsonify({"message":f"@{user.username} blocked."})
    
@app.route("/settings/unblock", methods=["POST"])
@auth_required
@validate_formkey
def settings_unblock_user(v):

    user=get_user(request.values.get("username"))

    x= v.has_block(user)
    if not x:
        abort(409)

    g.db.delete(x)

    cache.delete_memoized(v.idlist)
    #cache.delete_memoized(Board.idlist, v=v)
    cache.delete_memoized(frontlist, v=v)
    
    return jsonify({"message":f"@{user.username} unblocked."})


@app.route("/settings/block_guild", methods=["POST"])
@auth_required
@validate_formkey
def settings_block_guild(v):

    board=get_guild(request.values.get("board"), graceful=True)

    if not board:
        return jsonify({"error":"That guild doesn't exist."}), 404

    if v.has_blocked_guild(board):
        return jsonify({"error":f"You have already blocked +{board.name}."}), 409


    new_block=BoardBlock(user_id=v.id,
                        board_id=board.id,
                        created_utc=int(time.time())
                        )
    g.db.add(new_block)

    cache.delete_memoized(v.idlist)
    #cache.delete_memoized(Board.idlist, v=v)
    cache.delete_memoized(frontlist, v=v)

    return jsonify({"message":f"+{board.name} added to filter"})
    
@app.route("/settings/unblock_guild", methods=["POST"])
@auth_required
@validate_formkey
def settings_unblock_guild(v):

    board=get_guild(request.values.get("board"), graceful=True)

    x= v.has_blocked_guild(board)
    if not x:
        abort(409)

    g.db.delete(x)

    cache.delete_memoized(v.idlist)
    #cache.delete_memoized(Board.idlist, v=v)
    cache.delete_memoized(frontlist, v=v)
    
    return jsonify({"message":f"+{board.name} removed from filter"})

@app.route("/settings/apps", methods=["GET"])
@auth_required
def settings_apps(v):

    return render_template("settings_apps.html", v=v)