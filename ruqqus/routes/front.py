import time
from flask import *
from sqlalchemy import *
from sqlalchemy.orm import lazyload
import random

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

    comments=get_comments(cids, v=v, sort_type="new", load_parent=True)

    listing=[]
    for c in comments:
        c._is_blocked=False
        c._is_blocking=False
        c.replies=[]
        if c.author_id==1:
            c._is_system=True
            listing.append(c)
        elif c.parent_comment and c.parent_comment.author_id==v.id:
            c._is_comment_reply=True
            parent=c.parent_comment

            if parent in listing:
                parent.replies=parent.replies+[c]
            else:
                parent.replies=[c]
                listing.append(parent)

        elif c.parent.author_id==v.id:
            c._is_post_reply=True
            listing.append(c)
        else:
            c._is_username_mention=True
            listing.append(c)


    return render_template("notifications.html",
                           v=v,
                           notifications=listing,
                           next_exists=next_exists,
                           page=page,
                           standalone=True,
                           render_replies=True,
                           is_notification_page=True)

@cache.memoize(timeout=900)
def frontlist(v=None, sort="hot", page=1, nsfw=False, t=None, ids_only=True, **kwargs):

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

    posts = g.db.query(Submission
        ).options(lazyload('*')).filter_by(is_banned=False,
        is_deleted=False,
        stickied=False)

    if not nsfw:
        posts=posts.filter_by(over_18=False)

    if v and v.hide_offensive:
        posts.filter_by(is_offensive=False)

    if v and v.admin_level >= 4:
        board_blocks = g.db.query(BoardBlock.board_id).filter_by(user_id=v.id).subquery()

        posts=posts.filter(Submission.board_id.notin_(board_blocks))
    elif v:
        m=g.db.query(ModRelationship.board_id).filter_by(user_id=v.id, invite_rescinded=False).subquery()
        c=g.db.query(ContributorRelationship.board_id).filter_by(user_id=v.id).subquery()

        posts=posts.filter(
          or_(
            Submission.author_id==v.id,
            Submission.post_public==True,
            Submission.board_id.in_(m),
            Submission.board_id.in_(c)
            )
          )

        blocking=g.db.query(UserBlock.target_id).filter_by(user_id=v.id).subquery()
        blocked= g.db.query(UserBlock.user_id).filter_by(target_id=v.id).subquery()

        posts=posts.filter(
            Submission.author_id.notin_(blocking),
            Submission.author_id.notin_(blocked)
            )

        board_blocks = g.db.query(BoardBlock.board_id).filter_by(user_id=v.id).subquery()

        posts=posts.filter(Submission.board_id.notin_(board_blocks))
    else:
        posts=posts.filter_by(post_public=True)


    #board opt out of all
    if v:
        posts=posts.join(Submission.board).filter(
            or_(
                Board.all_opt_out==False,
                Submission.board_id.in_(
                    g.db.query(Subscription.board_id).filter_by(user_id=v.id, is_active=True).subquery()
                    )
                )
            ).options(contains_eager(Submission.board))
    else:
        posts=posts.join(Submission.board).filter_by(all_opt_out=False).options(contains_eager(Submission.board))



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
        posts=posts.order_by(Submission.score_best.desc())
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
@api("read")
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

                     #these arguments don't really do much but they exist for cache memoization differentiation
                     allow_nsfw=v.over_18,
                     hide_offensive=v.hide_offensive
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
@api("read")
def front_all(v):

    page=int(request.args.get("page") or 1)

    #prevent invalid paging
    page=max(page, 1)

    sort_method=request.args.get("sort", "hot")
    t=request.args.get('t','all')

    #get list of ids
    ids = frontlist(sort=sort_method,
                    page=page,
                    nsfw=(v and v.over_18 and not v.filter_nsfw),
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
        guilds=guilds.order_by(Board.stored_subscriber_count.desc())
    elif sort=="new":
        guilds=guilds.order_by(Board.created_utc.desc())
    elif sort=="trending":
        guilds=guilds.order_by(Board.rank_trending.desc())

    else:
        abort(422)

    guilds=[x.id for x in guilds.offset(25*(page-1)).limit(26).all()]
    

    return guilds

@app.route("/browse", methods=["GET"])
@app.route("/api/v1/guilds")
@auth_desired
@api("read")
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

    return {"html":lambda:render_template("boards.html",
                           v=v,
                           boards=boards,
                           page=page,
                           next_exists=next_exists,
                           sort_method=sort_method
                            ),
            "api":lambda:[board.json for board in boards]
            }

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
        content=content.order_by(Board.stored_subscriber_count.desc())
        
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

    x=g.db.query(Submission).options(lazyload('board')).filter_by(is_banned=False, is_deleted=False)

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
        bans=g.db.query(BanRelationship.id()).filter_by(user_id=v.id).all()
        x=x.filter(Submission.board_id.notin_([i[0] for i in bans]))

    total=x.count()
    n=random.randint(0, total-1)



    post = x.order_by(Submission.id.asc()).offset(n).limit(1).first()
    return redirect(post.permalink)

@app.route("/random/guild", methods=["GET"])
@auth_desired
def random_guild(v):

    x=g.db.query(Board).filter_by(
        is_banned=False, 
        is_private=False,
        over_18=False,
        is_nsfl=False)

    if v:
        bans=g.db.query(BanRelationship.id).filter_by(user_id=v.id).all()
        x=x.filter(Board.id.notin_([i[0] for i in bans]))


    total=x.count()
    n=random.randint(0, total-1)

    board=x.order_by(Board.id.asc()).offset(n).limit(1).first()

    return redirect(board.permalink)

@app.route("/random/comment", methods=["GET"])
@auth_desired
def random_comment(v):

    x=g.db.query(Comment).filter_by(is_banned=False,
        over_18=False,
        is_nsfl=False,
        is_offensive=False).filter(Comment.parent_submission.isnot(None))
    if v:
        bans=g.db.query(BanRelationship.id).filter_by(user_id=v.id).all()
        x=x.filter(Comment.board_id.notin_([i[0] for i in bans]))

    total=x.count()
    n=random.randint(0, total-1)
    comment=x.order_by(Comment.id.asc()).offset(n).limit(1).first()

    return redirect(comment.permalink)

@app.route("/random/user", methods=["GET"])
@auth_desired
def random_user(v):
    x=g.db.query(User).filter(or_(User.is_banned==0, and_(User.is_banned>0, User.unban_utc<int(time.time()))))

    x=x.filter_by(is_private=False)

    total=x.count()
    n=random.randint(0, total-1)

    user=x.offset(n).limit(1).first()

    return redirect(user.permalink)
