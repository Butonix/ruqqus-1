from urllib.parse import urlparse
import mistletoe
from sqlalchemy import func
from bs4 import BeautifulSoup

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.filters import *
from ruqqus.helpers.embed import *
from ruqqus.helpers.markdown import *
from ruqqus.classes import *
from flask import *
from ruqqus.__main__ import app, db

BAN_REASONS=['',
            "URL shorteners are not permitted."
            ]

@app.route("/api/is_available/<name>", methods=["GET"])
def api_is_available(name):
    if db.query(User.username).filter(User.username.ilike(name)).count():
        return jsonify({name:False})
    else:
        return jsonify({name:True})

@app.route("/uid/<uid>", methods=["GET"])
@admin_level_required(1)
def user_uid(uid, v):

    user=db.query(User).filter_by(id=base36decode(uid)).first()
    if user:
        return redirect(user.permalink)
    else:
        abort(404)

@app.route("/u/<username>", methods=["GET"])
@app.route("/u/<username>/posts", methods=["GET"])
@app.route("/@<username>", methods=["GET"])
@auth_desired
def u_username(username, v=None):
    
    #username is unique so at most this returns one result. Otherwise 404
    
    #case insensitive search

    result = db.query(User).filter(User.username.ilike(username)).first()

    if not result:
        abort(404)

    #check for wrong cases

    if username != result.username:
        return redirect(result.url)
        
    return result.rendered_userpage(v=v)

@app.route("/u/<username>/comments", methods=["GET"])
@app.route("/@<username>/comments", methods=["GET"])
@auth_desired
def u_username_comments(username, v=None):
    
    #username is unique so at most this returns one result. Otherwise 404
    
    #case insensitive search

    result = db.query(User).filter(User.username.ilike(username)).first()

    if not result:
        abort(404)

    #check for wrong cases

    if username != result.username:
        return redirect(result.url)
        
    return result.rendered_comments_page(v=v)
