import time
from flask import *
from sqlalchemy import *

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.get import *

from ruqqus.__main__ import app, cache
from ruqqus.classes.boards import Board


@app.route("/api/v1/guild/<boardname>", methods=["GET"])
@auth_desired
@api("read")
def guild_info(v, boardname):
    guild = get_guild(boardname)

    return jsonify(guild.json)


@app.route("/api/v1/user/<username>", methods=["GET"])
@auth_desired
@api("read")
def user_info(v, username):

    user = get_user(username, v=v)
    return jsonify(user.json)

@app.route('/api/v1/addfavorite/post/<pid>', methods=['GET'])
@auth_required
@api('read')
def addFavoritePost(pid, v):

    post = get_post(pid)

    if not post:
        abort(404)

    if not v.favorites.filter_by(post_id=post.id).first():
        new_fav = Favorite(user_id=v.id,
                           post_id=post.id)
        g.db.add(new_fav)

    else:
        return jsonify({"msg": "post has already been favorited"})

    return jsonify({"msg": "success"})


@app.route('/api/v1/removefavorite/post/<pid>', methods=['GET'])
@auth_required
@api('read')
def removeFavoritePost(pid, v):
    post = get_post(pid)

    if not post:
        abort(404)

    fav = v.favorites.filter_by(post_id=post.id).first()
    if fav:
        g.db.delete(fav)

    return jsonify({"msg": "success"})


@app.route('/api/v1/addfavorite/comment/<pid>', methods=['GET'])
@auth_required
@api('read')
def addFavoriteComment(cid, v):
    comment = get_comment(cid)

    if not comment:
        abort(404)

    if not v.favorites.filter_by(comment_id=comment.id).first():
        new_fav = Favorite(user_id=v.id,
                           comment_id=comment.id)
        g.db.add(new_fav)

    else:
        return jsonify({"msg": "post has already been favorited"})

    return jsonify({"msg": "success"})

@app.route('/api/v1/removefavorite/comment/<cid>', methods=['GET'])
@auth_required
@api('read')
def removeFavoriteComment(cid, v):
    comment = get_comment(cid)

    if not comment:
        abort(404)

    fav = v.favorites.filter_by(comment_id=comment.id).first()
    if fav:
        g.db.delete(fav)

    return jsonify({"msg": "success"})
