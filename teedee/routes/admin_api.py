from flask import *
from teedee.classes import *
from teedee.helpers.wrappers import *
from teedee.helpers.base36 import *
from secrets import token_hex
from teedee.__main__ import db, app

@app.route("/api/ban_user/<user_id>", methods=["POST"])
@admin_level_required(3)
@validate_formkey
def ban_user(user_id, v):

    user=db.query(User).filter_by(id=user_id).first()

    if not user:
        abort(400)

    user.is_banned=True

    db.add(user)
    db.commit()
    
    return redirect(user.url)

@app.route("/api/unban_user/<user_id>", methods=["POST"])
@admin_level_required(3)
@validate_formkey
def unban_user(user_id, v):

    user=db.query(User).filter_by(id=user_id).first()

    if not user:
        abort(400)

    user.is_banned=False

    db.add(user)
    db.commit()
    
    return redirect(user.url)

@app.route("/api/ban_post/<post_id>", methods=["POST"])
@admin_level_required(3)
@validate_formkey
def ban_post(post_id, v):

    post=db.query(Submission).filter_by(id=base36decode(post_id)).first()

    if not post:
        abort(400)

    post.is_banned=True
    post.stickied=False

    db.add(post)
    db.commit()
    
    return redirect(post.permalink)

@app.route("/api/unban_post/<post_id>", methods=["POST"])
@admin_level_required(3)
@validate_formkey
def unban_post(post_id, v):

    post=db.query(Submission).filter_by(id=base36decode(post_id)).first()

    if not post:
        abort(400)

    post.is_banned=False

    db.add(post)
    db.commit()
    
    return redirect(post.permalink)


@app.route("/api/promote/<user_id>/<level>", methods=["POST"])
@admin_level_required(3)
@validate_formkey
def promote(user_id, level, v):

    u = db.query(User).filter_by(id=user_id).first()
    if not u:
        abort(404)

    max_level_involved = max(level, u.admin_level)

    try:
        admin_level_needed={1:3, 2:3, 3:5, 4:5, 5:6}[max_level_involved]
    except KeyError:
        abort(400)

    if v.admin_level < admin_level_needed:
        abort(403)

    u.admin_level=level

    db.add(u)
    db.commit()

    return redirect(u.url)
    
    
@app.route("/api/distinguish/<post_id>", methods=["POST"])
@admin_level_required(3)
@validate_formkey
def api_distinguish_post(post_id, v):

    post=db.query(Submission).filter_by(id=base36decode(post_id)).first()

    if not post:
        abort(404)

    if not post.author_id == v.id:
        abort(403)

    if post.distinguish_level:
        post.distinguish_level=0
    else:
        post.distinguish_level=v.admin_level

    db.add(post)
    db.commit()

    return redirect(post.permalink)

@app.route("/api/sticky/<post_id>", methods=["POST"])
@admin_level_required(3)
def api_sticky_post(v):

    post=db.query(Submission).filter_by(id=base36decode(post_id)).first()

    already_stickied=post=db.query(Submission).filter_by(stickied=True).first()

    post.stickied=True
    
    if already_stickied:
        already_stickied.stickied=False
        db.add(already_stickied)
        
    db.add(post)
    db.commit()
