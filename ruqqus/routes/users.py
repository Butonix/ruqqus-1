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
from ruqqus.__main__ import app, db, cache, limiter

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

@app.route("/@<username>", methods=["GET"])
@app.route("/api/v1/user/<username>/listing", methods=["GET"])
@auth_desired
@api
def u_username(username, v=None):
    
    #username is unique so at most this returns one result. Otherwise 404
    
    #case insensitive search

    u = get_user(username)

    #check for wrong cases

    if username != u.username:
        return redirect(request.path.replace(username, u.username))
        

    if u.reserved:
        return {'html': lambda:render_template("userpage_reserved.html",
                                               u=u,
                                               v=v),
                'api': lambda:{"error":"That user is banned"}
                }

    if u.is_suspended and (not v or v.admin_level < 3):
        return {'html': lambda:render_template("userpage_banned.html",
                                               u=u,
                                               v=v),
                'api': lambda:{"error":"That user is banned"}
                }

    if u.is_private and (not v or (v.id!=u.id and v.admin_level<3)):
        return {'html': lambda:render_template("userpage_private.html",
                                               u=u,
                                               v=v),
                'api': lambda:{"error":"That userpage is private"}
                }

    page=int(request.args.get("page","1"))
    page=max(page, 1)

    ids=u.userpagelisting(v=v, page=page)

    
    
    #we got 26 items just to see if a next page exists
    next_exists=(len(ids)==26)
    ids=ids[0:25]

    listing=get_posts(ids, v=v, sort="new")

    return {'html': lambda:render_template("userpage.html",
                           u=u,
                           v=v,
                           listing=listing,
                           page=page,
                           next_exists=next_exists,
                           is_following=(v and u.has_follower(v))),
            'api': lambda:[x.json for x in listing]
            }

@app.route("/@<username>/comments", methods=["GET"])
@auth_desired
def u_username_comments(username, v=None):
    
    #username is unique so at most this returns one result. Otherwise 404
    
    #case insensitive search

    user=get_user(username)

    #check for wrong cases

    if username != user.username:
        return redirect(f'{user.url}/comments')
        
    if user.reserved:
        return render_template("userpage_reserved.html", u=user, v=v)

    if user.is_suspended and (not v or v.admin_level < 3):
        return render_template("userpage_banned.html", u=user, v=v)

    if user.is_private and (not v or (v.id!=user.id and v.admin_level<3)):
        return render_template("userpage_private.html", u=user, v=v)
    
    page=int(request.args.get("page","1"))

    ids=user.commentlisting(v=v, page=page)


    #we got 26 items just to see if a next page exists
    next_exists=(len(ids)==26)
    ids=ids[0:25]

    listing=get_comments(ids, v=v)

    is_following=(v and user.has_follower(v))
    
    return render_template("userpage_comments.html",
                           u=user,
                           v=v,
                           listing=listing,
                           page=page,
                           next_exists=next_exists,
                           is_following=is_following)

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
@limiter.exempt
def user_profile(username):
    x=get_user(username)
    return redirect(x.profile_url)

