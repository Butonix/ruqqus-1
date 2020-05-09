from ruqqus.classes import *
from ruqqus.helpers.wrappers import *

from sqlalchemy import *

from flask import *
from ruqqus.__main__ import app, db, cache

@cache.memoize(300)
def searchlisting(q, v=None, page=1, sort="hot"):

    posts = db.query(Submission).filter(func.lower(Submission.title).contains(q.lower()))


    if not (v and v.over_18):
        posts=posts.filter_by(over_18=False)

    if v and v.hide_offensive:
        posts=posts.filter_by(is_offensive=False)

    if not(v and v.admin_level>=3):
        posts=posts.filter_by(is_deleted=False, is_banned=False)

    if sort=="hot":
        posts=posts.order_by(Submission.score_hot.desc())
    elif sort=="new":
        posts=posts.order_by(Submission.created_utc.desc())
    elif sort=="fiery":
        posts=posts.order_by(Submission.score_fiery.desc())
    elif sort=="top":
        posts=posts.order_by(Submission.score_top.desc())
        
    total=posts.count()
    posts=[x for x in posts.offset(25*(page-1)).limit(26).all()]

    return total, [x.id for x in posts]

@app.route("/search", methods=["GET"])
@auth_desired
def search(v, search_type="posts"):

    query=request.args.get("q")


    page=max(1, int(request.args.get("page", 1)))


    if query.startswith("+"):

        #guild search stuff here
        sort=request.args.get("sort", "subs").lower()

        boards = db.query(Board).filter(func.lower(Board.name).contains(query.lstrip("+").lower()))

        if not(v and v.over_18):
            boards=boards.filter_by(over_18=False)

        if not (v and v.admin_level >= 3):
            boards=boards.filter_by(is_banned=False)

        boards=boards.order_by(Board.subscriber_count.desc())

        total=boards.count()

        boards=[x for x in boards.offset(25*(page-1)).limit(26)]
        next_exists=(len(boards)==26)
        boards=boards[0:25]
        
        return render_template("search_boards.html",
                               v=v,
                               query=query,
                               total=total,
                               page=page,
                               boards=boards,
                               sort_method=sort,
                               next_exists=next_exists
                               )
        

    else:
        sort=request.args.get("sort", "hot").lower()

        #posts search

        total, ids = searchlisting(query, v=v, page=page, sort=sort)
        
        next_exists=(len(ids)==26)
        ids=ids[0:25]

        posts=get_posts(ids, v=v)

        return render_template("search.html",
                               v=v,
                               query=query,
                               total=total,
                               page=page,
                               listing=posts,
                               sort_method=sort,
                               next_exists=next_exists
                               )
