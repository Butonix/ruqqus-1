import time
from flask import *
from sqlalchemy import *

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.get import *

from ruqqus.__main__ import app, db, cache
from ruqqus.classes.submission import Submission


@app.route("/post/", methods=["GET"])
def slash_post():
    return redirect("/")

@app.route("/notifications", methods=["GET"])
@auth_required
def notifications(v):

    page=int(request.args.get('page',1))
    all_=request.args.get('all', False)

    cids=v.notification_commentlisting(page=page,
        all_=all_
        )
    next_exists=(len(cids)==26)
    cids=cids[0:25]

    comments=get_comments(cids, v=v, sort_type="new")

    return render_template("notifications.html",
                           v=v,
                           notifications=comments,
                           next_exists=next_exists,
                           page=page)

@cache.memoize(timeout=300)
def frontlist(sort="hot", page=1, nsfw=False, t=None, v=None, hide_offensive=False, ids_only=True):

    #cutoff=int(time.time())-(60*60*24*30)

    posts = db.query(Submission).filter_by(is_banned=False,
                                           is_deleted=False,
                                           stickied=False)
    if not nsfw:
        posts=posts.filter_by(over_18=False)

    if hide_offensive:
        posts=posts.filter_by(is_offensive=False)

    if v and v.admin_level >= 4:
        pass
    elif v:
        m=v.moderates.filter_by(invite_rescinded=False).subquery()
        c=v.contributes.subquery()
        posts=posts.join(m,
                         m.c.board_id==Submission.board_id,
                         isouter=True
                         ).join(c,
                                c.c.board_id==Submission.board_id,
                                isouter=True
                                )
        posts=posts.filter(or_(Submission.author_id==v.id,
                               Submission.is_public==True,
                               m.c.board_id != None,
                               c.c.board_id !=None))
    else:
        posts=posts.filter_by(is_public=True)



    if t:
        now=int(time.time())
        if t=='day':
            cutoff=now-86400
        elif t=='week':
            cutoff=now-604800
        elif t=='month':
            cutoff=now-2592000
        elif t=='year':
            cutoff=now-31536000
        else:
            cutoff=0        
        posts=posts.filter(Submission.created_utc >= cutoff)

        
    if sort=="hot":
        posts=posts.order_by(Submission.score_hot.desc())
    elif sort=="new":
        posts=posts.order_by(Submission.created_utc.desc())
    elif sort=="disputed":
        posts=posts.order_by(Submission.score_disputed.desc())
    elif sort=="top":
        posts=posts.order_by(Submission.score_top.desc())
    elif sort=="activity":
        posts=posts.order_by(Submission.score_activity.desc())
    else:
        abort(422)

    if ids_only:
        posts=[x.id for x in posts.offset(25*(page-1)).limit(26).all()]
        return posts
    else:
        return [x for x in posts.offset(25*(page-1)).limit(25).all()]

@app.route("/", methods=["GET"])
@app.route("/api/v1/front/listing", methods=["GET"])
@auth_desired
@api
def home(v):

    if v and v.subscriptions.filter_by(is_active=True).count():

        only=request.args.get("only",None)
        sort=request.args.get("sort","hot")
        
        page=max(int(request.args.get("page",1)),0)
        t=request.args.get('t', 'all')
        
        ids=v.idlist(sort=sort,
                     page=page,
                     only=only,
                     t=t,
                     hide_offensive = v.hide_offensive
                     )

        next_exists=(len(ids)==26)
        ids=ids[0:25]

        #If page 1, check for sticky
        if page==1:
            sticky =[]
            sticky=db.query(Submission.id).filter_by(stickied=True).first()[0]
            if sticky:
                ids=[sticky]+ids

        posts=get_posts(ids, sort=sort, v=v)
        


        return {'html':lambda:render_template("subscriptions.html",
                               v=v,
                               listing=posts,
                               next_exists=next_exists,
                               sort_method=sort,
                               time_filter=t,
                               page=page,
                               only=only),
                'api':lambda:[x.json for x in posts]
                }
    else:
        return front_all()

@app.route("/all", methods=["GET"])
@app.route("/api/v1/all/listing", methods=["GET"])
@app.route("/inpage/all")
@auth_desired
@api
def front_all(v):

    page=int(request.args.get("page",1))

    #prevent invalid paging
    page=max(page, 1)

    sort_method=request.args.get("sort", "hot")
    t=request.args.get('t','all')

    #get list of ids
    ids = frontlist(sort=sort_method,
                    page=page,
                    nsfw=(v and v.over_18),
                    t=t,
                    v=v,
                    hide_offensive= v and v.hide_offensive
                    )

    #check existence of next page
    next_exists=(len(ids)==26)
    ids=ids[0:25]

   #If page 1, check for sticky
    if page==1:
        sticky =[]
        sticky=db.query(Submission.id).filter_by(stickied=True).first()
        if sticky:
            ids=[sticky]+ids
    #check if ids exist
    posts=get_posts(ids, sort=sort_method, v=v)
    
    return {'html':lambda:render_template("home.html",
                           v=v,
                           listing=posts,
                           next_exists=next_exists,
                           sort_method=sort_method,
                           time_filter=t,
                           page=page #,
                        #   trending_boards = trending_boards(n=5)
                           ),
            'inpage':lambda:render_template("submission_listing.html",
                                            v=v,
                                            listing=posts
                                            ),
            'api':lambda:[x.json for x in posts]
            }

@cache.memoize(600)
def guild_ids(sort="subs", page=1, nsfw=False):
    #cutoff=int(time.time())-(60*60*24*30)

    guilds = db.query(Board).filter_by(is_banned=False)

    if not nsfw:
        guilds=guilds.filter_by(over_18=False)

    if sort=="subs":
        guilds=guilds.order_by(Board.subscriber_count.desc())
    elif sort=="new":
        guilds=guilds.order_by(Board.created_utc.desc())
    elif sort=="trending":
        guilds=guilds.order_by(Board.trending_rank.desc())

    else:
        abort(422)

    guilds=[x.id for x in guilds.offset(25*(page-1)).limit(26).all()]
    

    return guilds

@app.route("/browse", methods=["GET"])
@auth_desired
def browse_guilds(v):

    page=int(request.args.get("page",1))

    #prevent invalid paging
    page=max(page, 1)

    sort_method=request.args.get("sort", "trending")

    #get list of ids
    ids = guild_ids(sort=sort_method, page=page, nsfw=(v and v.over_18))

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
        
        boards=db.query(Board
                       ).from_statement(
                           text(f"""
                            select *
                            from boards
                            join (values {tups}) as x(id, n)
                            on boards.id=x.id
                            where x.n is not null
                            order by x.n"""
                                )).all()
    else:
        boards=[]

    return render_template("boards.html",
                           v=v,
                           boards=boards,
                           page=page,
                           next_exists=next_exists,
                           sort_method=sort_method
                            )

@app.route('/mine', methods=["GET"])
@auth_required
def my_subs(v):

    kind=request.args.get("kind", "guilds")
    page=max(int(request.args.get("page", 1)),1)

    if kind=="guilds":

        b=db.query(Board)
        contribs=v.contributes.subquery()
        m=v.moderates.filter_by(accepted=True).subquery()
        s=v.subscriptions.filter_by(is_active=True).subquery()
        
        content=b.join(s,
                     Board.id==s.c.board_id,
                     isouter=True
              ).join(contribs,
                     contribs.c.board_id==Board.id,
                     isouter=True
              ).join(m,
                     m.c.board_id==Board.id,
                     isouter=True)
        

        content=content.filter(or_(s.c.id!=None,
                                   contribs.c.id != None,
                                   m.c.id != None
                                   )
                               )
        content=content.order_by(Board.subscriber_count.desc())
        
        content=[x for x in content.offset(25*(page-1)).limit(26)]
        next_exists=(len(content)==26)
        content=content[0:25]

        return render_template("mine/boards.html",
                               v=v,
                               boards=content,
                               next_exists=next_exists,
                               page=page,
                               kind="guilds")

    elif kind=="users":

        u=db.query(User)
        follows=v.following.subquery()

        content=u.join(follows,
                       User.id==follows.c.target_id,
                       isouter=False)

        content=content.order_by(User.follower_count.desc())

        content=[x for x in content.offset(25*(page-1)).limit(26)]
        next_exists=(len(content)==26)
        content=content[0:25]

        return render_template("mine/users.html",
                               v=v,
                               users=content,
                               next_exists=next_exists,
                               page=page,
                               kind="users")
        
    else:
        abort(422)

