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
    return redirect("/settings/profile")

@app.route("/settings/profile", methods=["GET"])
@auth_required
def settings_profile(v):
    return render_template("settings_profile.html", v=v)

@app.route("/settings/security", methods=["GET"])
@auth_required
def settings_security(v):
    return render_template("settings_security.html", v=v)

@app.route("/help", methods=["GET"])
@auth_desired
def help(v):
    return redirect("/help/terms")

@app.route("/favicon.ico", methods=["GET"])
def favicon():
    return send_file("./assets/images/logo/favicon.png")

@app.route("/my_info",methods=["GET"])
@auth_required
def my_info(v):
    return render_template("my_info.html", v=v)

@app.route("/notifications", methods=["GET"])
@auth_required
def notifications(v):
    return v.notifications_page(page=request.args.get("page","1"),
                                   include_read=request.args.get("all",False))

@app.route("/submit", methods=["GET"])
@is_not_banned
def submit_get(v):
    return render_template("submit.html", v=v)

@app.route("/about/<path:path>")
def about_path(path):
    return redirect(f"/help/{path}")

@app.route("/help/<path:path>")
@auth_desired
def help_path(path, v):
    return render_template(safe_join("help", path+".html"), v=v)
