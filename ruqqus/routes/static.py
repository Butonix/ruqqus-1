import time
from ruqqus.helpers.wrappers import *
from flask import *

from ruqqus.__main__ import app
from ruqqus.classes import *

#take care of misc pages that never really change (much)
@app.route('/assets/<path:path>')
def static_service(path):
    return send_from_directory('./assets', path)

@app.route("/robots.txt", methods=["GET"])
def robots_txt():
    return send_file("./assets/robots.txt")

@app.route("/settings", methods=["GET"])
@auth_required
def settings(v):
    return render_template("settings.html", v=v)

@app.route("/favicon.ico", methods=["GET"])
def favicon():
    return send_file("./assets/images/favicon.ico")

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
