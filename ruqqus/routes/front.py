import time
from flask import *
from sqlalchemy import *

from ruqqus.helpers.wrappers import *

from ruqqus.__main__ import app, db, cache
from ruqqus.classes.submission import Submission


@cache.memoize(timeout=30)
def frontlist(sort="hot", page=1):

    #cutoff=int(time.time())-(60*60*24*30)

    posts = db.query(Submission).filter(#Submission.created_utc>=cutoff,
                                        Submission.is_banned==False,
                                        Submission.is_deleted==False,
                                        Submission.stickied==False)

    if sort=="hot":
        posts=posts.order_by(text("submissions.rank_hot desc"))
    elif sort=="new":
        posts=posts.order_by(Submission.created_utc.desc())
    elif sort=="disputed":
        posts=posts.order_by(text("submissions.rank_fiery desc"))
    elif sort=="top":
        posts=posts.order_by(text("submissions.score desc"))
    elif sort=="activity":
        posts=posts.order_by(text("submissions.rank_activity desc"))

    posts=[x.id for x in posts.offset(25*(page-1)).limit(26).all()]
    

    return posts
    


@app.route("/", methods=["GET"])
@auth_desired
def home(v):

    page=int(request.args.get("page",1))

    #prevent invalid paging
    page=max(page, 1)

    sort_method=request.args.get("sort", "hot")

    #get list of ids
    ids = frontlist(sort=sort_method, page=page)

    #check existence of next page
    next_exists=(len(ids)==26)
    ids=ids[0:25]

    #check if ids exist
    if ids:
        #assemble list of tuples
        i=1
        tups=[]
        for x in ids:
            tups.append((x, i))
            i+=1

        #tuple string
        tups = str(tups).lstrip("[").rstrip("]")
            

        #hit db for entries
        
        posts=db.query(Submission
                       ).from_statement(
                           text(f"""
                            select submissions.*, submissions.ups, submissions.downs
                            from submissions
                            join (values {tups}) as x(id, n) on submissions.id=x.id order by x.n"""
                                )).all()
    else:
        posts=[]

    

    #If page 1, check for sticky
    if page==1:
        sticky =[]
        sticky=db.query(Submission).filter_by(stickied=True).first()
        if sticky:
            posts=[sticky]+posts
    
    return render_template("home.html", v=v, listing=posts, next_exists=next_exists, sort_method=sort_method, page=page)
