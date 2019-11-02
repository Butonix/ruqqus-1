import praw
from os import environ
from flask import *
from ruqqus.classes import *
from ruqqus.helpers.wrappers import *
from secrets import token_hex
from ruqqus.__main__ import db, app

r=praw.Reddit(client_id=environ.get("reddit_id"),
              client_secret=environ.get("reddit_secret"),
              user_agent="ruqqus username verification by /u/captainmeta4",
              redirect_uri="https://www.ruqqus.com/api/redditredirect")

@app.route("/api/get_reddit_auth", methods=["GET"])
@auth_required
def api_get_reddit_auth(v):
    return redirect(r.auth.url(scopes=["identity"],
                               state=session["session_id"],
                               duration="temporary"))

@app.route("/api/redditredirect", methods=["GET"])
@auth_required
def api_redditredirect(v):

    if v.reddit_username:
        return render_template("settings.html", v=v, error=f"You are already linked to the reddit account /u/{v.reddit_username}.")

    #check session id
    if not request.args.get("state")==session["session_id"]:
        return render_template("settings.html", v=v, error="Invalid token. Please close this page and try again later.")

        
    try:
        r.auth.authorize(request.args.get("code"))
        name = r.user.me().name
    except Exception as e:
        print(e)
        return render_template("settings.html", v=v, error="Unable to check reddit username.")

    #check for existing
    existing = db.query(User).filter(User.reddit_username == name,
                                     User.id != v.id
                                     ).first()
    if existing:
        return render_template("settings.html", v=v, error=f"The reddit account {name} is already tied to a different Ruqqus account.")
    
    v.reddit_username = name

    #assign reddit badge
    reddit_badge = Badge(user_id=v.id,
                         badge_id=5,
                         url=f"https://reddit.com/user/{name}",
                         description=f"/u/{name}"
                         )
    
    db.add(v)
    db.add(reddit_badge)
    db.commit()

    return render_template("settings.html", v=v, msg=f"Reddit account {name} successfully linked.")
    
@app.route("/api/del_reddit_name", methods=["POST"])
@auth_required
@validate_formkey
def api_del_reddit_name(v):

    if not v.reddit_username:
        render_template("settings_profile.html", v=v, error=f"You didn't have a reddit account to un-link.")

    v.reddit_username=None

    #delete reddit badge
    for badge in v.badges:
        if badge.type==5:
            db.delete(badge)
            
    db.add(v)
    db.commit()
    return render_template("settings_profile.html", v=v, msg=f"Reddit account successfully un-linked.")
