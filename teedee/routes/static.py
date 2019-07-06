from teedee.__main__ import app
from teedee.helpers.wrappers import *
from flask import *

#take care of static pages
@app.route('/static/<path:path>')
def static_service(path):
    return send_from_directory('./static', path)

@app.route("/robots.txt", methods=["GET"])
def robots_txt():
    return send_from_directory("./static", "robots.txt")
