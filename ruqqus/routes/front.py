import time
from flask import *
from sqlalchemy import *

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.get import *

from ruqqus.__main__ import app, cache
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
                           page=page,
                           standalone=True)

@cache.memoize(timeout=900)
def frontlist(sort="hot", page=1, nsfw=False, t=None, v=None, ids_only=True, **kwargs):

    #cutoff=int(time.time())-(60*60*24*30)


    if sort=="hot":
        sort_func=Submission.score_hot.desc
    elif sort=="new":
        sort_func=Submission.created_utc.desc
    elif sort=="disputed":
        sort_func=Submission.score_disputed.desc
    elif sort=="top":
        sort_func=Submission.score_top.desc
    elif sort=="activity":
        sort_func=Submission.score_activity.desc
    else:
        abort(422)

    posts = g.db.query(Submission,
        func.rank().over(
            partition_by=Submission.board_id,
            order_by=sort_func()
            ).label("rn")
        ).filter_by(is_banned=False,
        is_deleted=False,
        stickied=False)

    if not (v and v.over_18):
        posts=posts.filter_by(over_18=False)

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

        blocking=v.blocking.subquery()
        blocked=v.blocked.subquery()
        posts=posts.join(blocking,
            blocking.c.target_id==Submission.author_id,
            isouter=True).join(blocked,
                blocked.c.user_id==Submission.author_id,
                isouter=True).filter(
                    blocking.c.id==None,
                    blocked.c.id==None)
    else:
        posts=posts.filter_by(post_public=True)



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

    posts_subquery=posts.subquery()

    if sort=="hot":
        posts=g.db.query(posts_subquery).filter(posts_subquery.c.rn<=2)
    else:
        posts=g.db.query(posts_subquery)

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
        if page==1 and sort != "new":
            sticky=g.db.query(Submission.id).filter_by(stickied=True).first()
            if sticky:
                ids=[sticky.id]+ids


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

    page=int(request.args.get("page") or 1)

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
        sticky=g.db.query(Submission.id).filter_by(stickied=True).first()
        if sticky:
            ids=[sticky.id]+ids
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

    guilds = g.db.query(Board).filter_by(is_banned=False)

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
        
        boards=g.db.query(Board
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

        b=g.db.query(Board)
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

        u=g.db.query(User)
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

@app.route("/random/post", methods=["GET"])
@auth_desired
def random_post(v):

    x=g.db.query(Submission).filter_by(is_banned=False, is_deleted=False)

    now=int(time.time())
    cutoff=now - (60*60*24*180)
    x=x.filter(Submission.created_utc>=cutoff)

    if not (v and v.over_18):
        x=x.filter_by(over_18=False)

    if not (v and v.show_nsfl):
        x=x.filter_by(is_nsfl=False)

    if v and v.hide_offensive:
        x=x.filter_by(is_offensive=False)

    if v:
        bans=g.db.query(BanRelationship.id).filter_by(user_id=v.id).all()
        x=x.filter(Submission.board_id.notin_([i[0] for i in bans]))

    post = x.order_by(func.random()).first()
    return redirect(post.permalink)

@app.route("/random/guild", methods=["GET"])
@auth_desired
def random_guild(v):

    x=g.db.query(Board).filter_by(is_banned=False, 
        is_private=False,
        over_18=False,
        is_nsfl=False)

    if v:
        bans=g.db.query(BanRelationship.id).filter_by(user_id=v.id).all()
        x=x.filter(Board.id.notin_([i[0] for i in bans]))

    board=x.order_by(func.random()).first()

    return redirect(board.permalink)

@app.route("/random/comment", methods=["GET"])
@auth_desired
def random_comment(v):

    x=g.db.query(Comment).filter_by(is_banned=False,
        over_18=False,
        is_nsfl=False,
        is_offensive=False)
    if v:
        bans=g.db.query(BanRelationship.id).filter_by(user_id=v.id).all()
        x=x.filter(Comment.board_id.notin_([i[0] for i in bans]))
    comment=x.order_by(func.random()).first()

    return redirect(comment.permalink)

@app.route("/random/user", methods=["GET"])
@auth_desired
def random_user(v):
    x=g.db.query(User).filter(or_(User.is_banned==0, and_(User.is_banned>0, User.unban_utc<int(time.time()))))

    x=x.filter_by(is_private=False)
    user=x.order_by(func.random()).first()

    return redirect(user.permalink)
