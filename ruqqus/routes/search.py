from ruqqus.classes import *
from ruqqus.helpers.wrappers import *

from sqlalchemy import *

from flask import *
from ruqqus.__main__ import app, db

@app.route("/search", methods=["GET"])
@auth_desired
def search(v, search_type="posts"):

    query=request.args.get("q")
    sort=request.args.get("sort", "hot").lower()

    page=max(1, int(request.args.get("page", 1)))


    if search_type == "posts":
        columns = [Submission.title, Submission.body]
    elif search_type == "users":
        columns = [User.username]
    elif search_type == "guilds":
        columns = [Board.description, Board.name, Board.submissions]

    keywords = query.lower().split()
    conditions = [func.lower(column).contains(word) for word in keywords for column in columns]
    conditions = tuple(conditions)
    posts = db.query(Submission).filter(or_(*conditions))


    if not (v and v.over_18):
        posts=posts.filter_by(over_18=False)

    if not(v and v.admin_level>=3):
        posts=posts.filter_by(is_deleted=False, is_banned=False)

    if sort=="hot":
        posts=posts.order_by(text("submissions.rank_hot desc"))
    elif sort=="new":
        posts=posts.order_by(Submission.created_utc.desc())
    elif sort=="fiery":
        posts=posts.order_by(text("submissions.rank_fiery desc"))
    elif sort=="top":
        posts=posts.order_by(text("submissions.score desc"))
        
    total=posts.count()
    posts=[x for x in posts.offset(25*(page-1)).limit(26).all()]
    
    next_exists=(len(posts)==26)
    results=posts[0:25]

    return render_template("search.html", v=v, query=query, total=total, page=page, listing=results, sort_method=sort, next_exists=next_exists)
