from ruqqus.classes import *
from ruqqus.helpers.wrappers import *

from ruqqus.__main__ import app, db

@app.route("/flagged/posts", methods=["GET"])
@admin_level_required(3)
def flagged_posts(v):

    page=max(1, int(request.args.get("page", 1)))

    posts = db.query(Submission).filter_by(is_approved=0, is_banned=False).filter(Submission.flag_count>=1).order_by(text("submissions.flag_count desc")).offset(25*(page-1)).limit(26)

    listing=[p for p in posts]
    next_exists=(len(listing)==26)
    listing=listing[0:25]

    return render_template("flagged_posts.html", next_exists=next_exists, listing=listing, page=page, v=v)


@app.route("/flagged/comments", methods=["GET"])
@admin_level_required(3)
def flagged_comments(v):

    page=max(1, int(request.args.get("page", 1)))

    posts = db.query(Comment).filter_by(is_approved=0, is_banned=False).filter(Comment.flag_count>=1).order_by(text("comments.flag_count desc")).offset(25*(page-1)).limit(26)

    listing=[p for p in posts]
    next_exists=(len(listing)==26)
    listing=listing[0:25]

    return render_template("flagged_comments.html", next_exists=next_exists, listing=listing, page=page, v=v)
