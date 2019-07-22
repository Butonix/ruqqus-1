from time import time
from ruqqus.helpers.wrappers import *
from flask import *

from ruqqus.__main__ import app
from ruqqus.classes import *

#take care of misc pages that never really change (much)

@app.route("/", methods=["GET"])
@auth_desired
def home(v):

    cutoff=int(time())-(60*60*24*30)

    posts = db.query(Submission).filter(Submission.created_utc>=cutoff,
                                        Submission.is_banned==False).all()

    sort_method=request.args.get("sort", "hot")

    if sort_method=="hot":
        posts.sort(key=lambda x: x.rank_hot, reverse=True)
    elif sort_method=="new":
        posts.sort(key=lambda x: x.created_utc, reverse=True)
    elif sort_method=="fiery":
        posts.sort(key=lambda x: x.rank_controversial, reverse=True)
    elif sort_method=="top":
        posts.sort(key=lambda x: x.score, reverse=True)

    #check for a sticky'

    for i in range(len(posts)):
        post=posts[i]
        if post.stickied:
            posts.insert(0, post)
            posts.pop(i+1)
            break
    else:
        sticky=db.query(Submission).filter(Submission.stickied==True).first()
        if sticky:
            listing=[sticky]+posts
    
    return render_template("home.html", v=v, listing=posts, sort_method=sort_method)

@app.route('/static/<path:path>')
def static_service(path):
    return send_from_directory('./static', path)

@app.route("/robots.txt", methods=["GET"])
def robots_txt():
    return send_from_directory("./static", "robots.txt")

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
def rules(v):
    return render_template("about.html", v=v)

@app.route("/terms",methods=["GET"])
@auth_desired
def terms(v):
    return render_template("terms.html", v=v)

@app.route("/my_info",methods=["GET"])
@auth_required
def my_info(v):
    return render_template("my_info.html", v=v)

@app.route("/submit", methods=["GET"])
@is_not_banned
def submit_get(v):
    return render_template("submit.html", v=v)
