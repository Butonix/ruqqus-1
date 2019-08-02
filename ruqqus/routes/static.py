import time
from ruqqus.helpers.wrappers import *
from flask import *

from ruqqus.__main__ import app
from ruqqus.classes import *

#take care of misc pages that never really change (much)

@app.route("/", methods=["GET"])
@auth_desired
def home(v):

    page=int(request.args.get("page",1))

    cutoff=int(time.time())-(60*60*24*30)

    posts = db.query(Submission).filter(Submission.created_utc>=cutoff,
                                        Submission.is_banned==False,
                                        Submission.stickied==False)

    sort_method=request.args.get("sort", "hot")

    if sort_method=="hot":
        posts=posts.order_by(Submission.rank_hot.desc())
    elif sort_method=="new":
        posts=posts.order_by(Submission.created_utc.desc())
    elif sort_method=="fiery":
        posts=posts.order_by(Submission.rank_fiery.desc())
    elif sort_method=="top":
        posts=posts.order_by(Submission.score.desc())

    #page
    posts=posts.offset(25*(page-1)).limit(25).all()
    

    #If page 1, check for sticky
    if page==1:
        sticky =[]
        sticky=db.query(Submission).filter_by(stickied=True).first()
        if sticky:
            posts=[sticky]+posts
    
    return render_template("home.html", v=v, listing=posts, sort_method=sort_method)

@app.route('/assets/<path:path>')
def static_service(path):
    return send_from_directory('./assets', path)

@app.route("/robots.txt", methods=["GET"])
def robots_txt():
    return send_from_directory("./assets", "robots.txt")

@app.route("/settings", methods=["GET"])
@auth_required
def settings(v):
    return render_template("settings.html", v=v)

@app.route("/rules",methods=["GET"])
@auth_desired
def rules(v):
    return render_template("rules.html", v=v)

@app.route("/about",methods=["GET"])
@auth_desired
def about(v):
    return render_template("about.html", v=v)

@app.route("/terms",methods=["GET"])
@auth_desired
def terms(v):
    return render_template("terms.html", v=v)

@app.route("/my_info",methods=["GET"])
@auth_required
def my_info(v):
    return render_template("my_info.html", v=v)

@app.route("/notifications", methods=["GET"])
@auth_required
def notifications(v):
    return v.notifications_unread(page=request.args.get("page","1"),
                                   include_read=request.args.get("all",False))

@app.route("/submit", methods=["GET"])
@is_not_banned
def submit_get(v):
    return render_template("submit.html", v=v)

@app.route("/favicon.ico")
def favicon_ico():
    return send_from_directory('./assets', "images/favicon.ico")
