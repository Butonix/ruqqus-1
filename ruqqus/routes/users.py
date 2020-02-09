from urllib.parse import urlparse
import mistletoe
from sqlalchemy import func
from bs4 import BeautifulSoup
import pyotp
import qrcode
import io

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.filters import *
from ruqqus.helpers.embed import *
from ruqqus.helpers.markdown import *
from ruqqus.helpers.get import *
from ruqqus.classes import *
from flask import *
from ruqqus.__main__ import app, db, cache

BAN_REASONS=['',
            "URL shorteners are not permitted."
            ]

@app.route("/2faqr/<secret>", methods=["GET"])
@auth_required
def mfa_qr(secret, v):
    x=pyotp.TOTP(secret)
    qr=qrcode.QRCode(
                error_correction=qrcode.constants.ERROR_CORRECT_L
    )
    qr.add_data(x.provisioning_uri(v.username, issuer_name="Ruqqus"))
    img=qr.make_image(fill_color="#603abb", back_color="white")
    
    mem=io.BytesIO()
            
    img.save(mem, format="PNG")
    mem.seek(0,0)
    return send_file(mem, mimetype="image/png", as_attachment=False)

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

@app.route("/api/follow/<username>", methods=["POST"])
@auth_required
def follow_user(username, v):

    target=get_user(username)

    #check for existing follow
    if db.query(Follow).filter_by(user_id=v.id, target_id=target.id).first():
        abort(409)

    new_follow=Follow(user_id=v.id,
                      target_id=target.id)

    db.add(new_follow)
    db.commit()

    cache.delete_memoized(User.idlist, v, kind="user")

    return "", 204


@app.route("/api/unfollow/<username>", methods=["POST"])
@auth_required
def unfollow_user(username, v):

    target=get_user(username)

    #check for existing follow
    follow= db.query(Follow).filter_by(user_id=v.id, target_id=target.id).first()

    if not follow:
        abort(409)

    db.delete(follow)
    db.commit()

    cache.delete_memoized(User.idlist, v, kind="user")

    return "", 204


@app.route("/api/agree_tos", methods=["POST"])
@auth_required
def api_agree_tos(v):

    v.tos_agreed_utc=int(time.time())

    db.add(v)
    db.commit()

    return redirect("/help/terms")


@app.route("/@<username>/pic/profile")
def user_profile(username):
    x=get_user(username)
    return redirect(x.profile_url)

