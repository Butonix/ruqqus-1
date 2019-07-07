from time import time
from teedee.helpers.wrappers import *
from flask import *

from teedee.__main__ import app
from teedee.classes import *

#take care of misc pages that never really change (much)

@app.route("/", methods=["GET"])
@auth_desired
def home(v):

    cutoff=int(time())-(60*60*24*30)

    posts = db.query(Submission).filter(Submission.created_utc>=cutoff).all()

    posts.sort(key=lambda x: x.rank_hot)
    
    return render_template("home.html", v=v, listing=posts)

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

@app.route("/submit", methods=["GET"])
@is_not_banned
def submit_get(v):
    return render_template("submit.html", v=v)
