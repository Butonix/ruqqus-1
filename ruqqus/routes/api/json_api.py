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
def guild_info(boardname):
    guild = get_guild(boardname)

    return jsonify(guild.json)


@app.route("/api/v1/user/<username>", methods=["GET"])
@auth_desired
@api("read")
def user_info(username):

    user=get_user(username)
    return jsonify(user.json)

@app.route("/api/v1/post/<pid>", methods=["GET"])
@auth_desired
@api("read")
def post_info(v, pid):

    post=get_post(pid)

    if not post.is_public and post.board.is_private and not post.board.can_view(v):
        abort(403)
        
    return jsonify(post.json)

@app.route("/api/v1/comment/<cid>", methods=["GET"])
@auth_desired
@api("read")
def comment_info(v, cid):

    comment=get_comment(cid)

    post=comment.post
    if not post or not post.is_public and post.board.is_private and not post.board.can_view(v):
        abort(403)
        
    return jsonify(comment.json)
