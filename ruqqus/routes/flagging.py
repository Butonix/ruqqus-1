import time
from ruqqus.classes import *
from ruqqus.helpers.wrappers import *
from ruqqus.helpers.base36 import*

from ruqqus.__main__ import app, db

@app.route("/api/flag/post/<pid>", methods=["POST"])
@is_not_banned
def api_flag_post(pid, v):

    pid=base36decode(pid)

    existing=db.query(Flag).filter_by(user_id=v.id, post_id=pid).first()

    if existing:
        abort(422)

    flag=Flag(post_id=pid,
              user_id=v.id,
              created_utc=int(time.time())
              )

    db.add(flag)

    db.commit()
    return "", 204


@app.route("/api/flag/comment/<cid>", methods=["POST"])
@is_not_banned
def api_flag_comment(cid, v):

    cid=base36decode(cid)

    existing=db.query(CommentFlag).filter_by(user_id=v.id, comment_id=cid).first()

    if existing:
        abort(422)

    flag=CommentFlag(comment_id=cid,
              user_id=v.id,
              created_utc=int(time.time())
              )

    db.add(flag)

    db.commit()
    return "", 204
