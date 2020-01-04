from urllib.parse import urlparse
from time import time

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.sanitize import *
from ruqqus.classes import *
from flask import *
from ruqqus.__main__ import app, db

@app.route("/api/vote/post/<post_id>/<x>", methods=["POST"])
@is_not_banned
@validate_formkey
def api_vote_post(post_id, x, v):

    
    if x not in ["-1", "0","1"]:
        abort(400)

    x=int(x)
    post_id=base36decode(post_id)

    post = db.query(Submission).filter_by(id=post_id).first()
    if not post:
        abort(404)

    if post.is_banned:
        abort(403)

    #check for existing vote
    existing = db.query(Vote).filter_by(user_id=v.id, submission_id=post_id).first()
    if existing:
        existing.change_to(x)
        return "", 204

    vote=Vote(user_id=v.id,
              vote_type=x,
              submission_id=post_id
              )

    db.add(vote)
    db.commit()

    return "", 204
                    
@app.route("/api/vote/comment/<comment_id>/<x>", methods=["POST"])
@is_not_banned
@validate_formkey
def api_vote_comment(comment_id, x, v):

    
    if x not in ["-1", "0","1"]:
        abort(400)

    x=int(x)
    comment_id=base36decode(comment_id)

    comment = db.query(Comment).filter_by(id=comment_id).first()
    if not comment_id:
        abort(404)

    if comment.is_banned:
        abort(403)

    #check for existing vote
    existing = db.query(CommentVote).filter_by(user_id=v.id, comment_id=comment_id).first()
    if existing:
        existing.change_to(x)
        return "", 204

    vote=CommentVote(user_id=v.id,
              vote_type=x,
              comment_id=comment_id
              )

    db.add(vote)
    db.commit()

    return "", 204
