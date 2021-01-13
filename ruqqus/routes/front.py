import time
from flask import *
from sqlalchemy import *
from sqlalchemy.orm import lazyload
import random

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.get import *

from ruqqus.__main__ import app, cache
from ruqqus.classes.submission import Submission
from ruqqus.classes.categories import CATEGORIES


@app.route("/post/", methods=["GET"])
def slash_post():
    return redirect("/")


@app.route("/notifications", methods=["GET"])
@auth_required
def notifications(v):

    page = int(request.args.get('page', 1))
    all_ = request.args.get('all', False)

    cids = v.notification_commentlisting(page=page,
                                         all_=all_
                                         )
    next_exists = (len(cids) == 26)
    cids = cids[0:25]

    comments = get_comments(cids, v=v, sort_type="new", load_parent=True)

    listing = []
    for c in comments:
        c._is_blocked = False
        c._is_blocking = False
        c.replies = []
        if c.author_id == 1:
            c._is_system = True
            listing.append(c)
        elif c.level > 1 and c.parent_comment and c.parent_comment.author_id == v.id:
            c._is_comment_reply = True
            parent = c.parent_comment

            if parent in listing:
                parent.replies = parent.replies + [c]
            else:
                parent.replies = [c]
                listing.append(parent)

        elif c.level == 1 and c.post.author_id == v.id:
            c._is_post_reply = True
            listing.append(c)
        else:
            c._is_username_mention = True
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

def frontlist(v=None, sort="hot", page=1, nsfw=False, nsfl=False,
              t=None, ids_only=True, categories=[], filter_words='', **kwargs):

    # cutoff=int(time.time())-(60*60*24*30)

    if sort == "hot":
        sort_func = Submission.score_hot.desc
    elif sort == "new":
        sort_func = Submission.created_utc.desc
    elif sort == "disputed":
        sort_func = Submission.score_disputed.desc
    elif sort == "top":
        sort_func = Submission.score_top.desc
    elif sort == "activity":
        sort_func = Submission.score_activity.desc
    else:
        abort(400)

    posts = g.db.query(
        Submission
        ).options(
            lazyload('*')
        ).filter_by(
            is_banned=False,
            stickied=False
        ).filter(Submission.deleted_utc == 0)

    if not nsfw:
        posts = posts.filter_by(over_18=False)
    
    if not nsfl:
	    posts = posts.filter_by(is_nsfl=False)

    if (v and v.hide_offensive) or not v:
        posts = posts.filter_by(is_offensive=False)

    if v and v.admin_level >= 4:
        board_blocks = g.db.query(
            BoardBlock.board_id).filter_by(
            user_id=v.id).subquery()

        posts = posts.filter(Submission.board_id.notin_(board_blocks))
    elif v:
        m = g.db.query(ModRelationship.board_id).filter_by(
            user_id=v.id, invite_rescinded=False).subquery()
        c = g.db.query(
            ContributorRelationship.board_id).filter_by(
            user_id=v.id).subquery()

        posts = posts.filter(
            or_(
                Submission.author_id == v.id,
                Submission.post_public == True,
                Submission.board_id.in_(m),
                Submission.board_id.in_(c)
            )
        )

        blocking = g.db.query(
            UserBlock.target_id).filter_by(
            user_id=v.id).subquery()
        blocked = g.db.query(
            UserBlock.user_id).filter_by(
            target_id=v.id).subquery()
        posts = posts.filter(
            Submission.author_id.notin_(blocking),
            Submission.author_id.notin_(blocked)
        )

        board_blocks = g.db.query(
            BoardBlock.board_id).filter_by(
            user_id=v.id).subquery()

        posts = posts.filter(Submission.board_id.notin_(board_blocks))
    else:
        posts = posts.filter_by(post_public=True)

    # board opt out of all
    if v:
        posts = posts.join(Submission.board).filter(
            or_(
                Board.all_opt_out == False,
                Submission.board_id.in_(
                    g.db.query(
                        Subscription.board_id).filter_by(
                        user_id=v.id,
                        is_active=True).subquery()
                )
            )
        )
    else:

        posts = posts.join(
            Submission.board).filter_by(
            all_opt_out=False)

    
    if categories:
        posts=posts.filter(Board.subcat_id.in_(tuple(categories)))

    posts=posts.options(contains_eager(Submission.board))


    #custom filter
    #print(filter_words)
    if v and filter_words:
        posts=posts.join(Submission.submission_aux)
        for word in filter_words:
            #print(word)
            posts=posts.filter(not_(SubmissionAux.title.ilike(f'%{word}%')))

    if t:
        now = int(time.time())
        if t == 'day':
            cutoff = now - 86400
        elif t == 'week':
            cutoff = now - 604800
        elif t == 'month':
            cutoff = now - 2592000
        elif t == 'year':
            cutoff = now - 31536000
        else:
            cutoff = 0
        posts = posts.filter(Submission.created_utc >= cutoff)

    gt = kwargs.get("gt")
    lt = kwargs.get("lt")

    if gt:
        posts = posts.filter(Submission.created_utc > gt)

    if lt:
        posts = posts.filter(Submission.created_utc < lt)

    if sort == "hot":
        posts = posts.order_by(Submission.score_best.desc())
    elif sort == "new":
        posts = posts.order_by(Submission.created_utc.desc())
    elif sort == "disputed":
        posts = posts.order_by(Submission.score_disputed.desc())
    elif sort == "top":
        posts = posts.order_by(Submission.score_top.desc())
    elif sort == "activity":
        posts = posts.order_by(Submission.score_activity.desc())
    else:
        abort(400)

    if ids_only:
        posts = [x.id for x in posts.offset(25 * (page - 1)).limit(26).all()]
        return posts
    else:
        return [x for x in posts.offset(25 * (page - 1)).limit(25).all()]


@app.route("/", methods=["GET"])
@app.route("/api/v1/front/listing", methods=["GET"])
@auth_desired
@api("read")
def home(v):

    if v and [i for i in v.subscriptions if i.is_active]:

        only=request.args.get("only",None)
        sort=request.args.get("sort","hot")
        
        page=max(int(request.args.get("page",1)),0)
        t=request.args.get('t', 'all')

        ignore_pinned = bool(request.args.get("ignore_pinned", False))

        
        ids=v.idlist(sort=sort,
                     page=page,
                     only=only,
                     t=t,
                     filter_words=v.filter_words,

                     # these arguments don't really do much but they exist for
                     # cache memoization differentiation
                       allow_nsfw=v.over_18,
                     hide_offensive=v.hide_offensive,
                     hide_politics=v and v.is_hiding_politics,

                     #greater/less than
                     gt=int(request.args.get("utc_greater_than",0)),
                     lt=int(request.args.get("utc_less_than",0)),

                     )

        next_exists=(len(ids)==26)
        ids=ids[0:25]

        # If page 1, check for sticky
        if page == 1 and sort != "new" and not ignore_pinned:
            sticky = g.db.query(Submission.id).filter_by(stickied=True).first()


            if sticky:
                ids=[sticky.id]+ids


        posts = get_posts(ids, sort=sort, v=v)

        return {'html': lambda: render_template("subscriptions.html",
                                                v=v,
                                                listing=posts,
                                                next_exists=next_exists,
                                                sort_method=sort,
                                                time_filter=t,
                                                page=page,
                                                only=only),
                'api': lambda: jsonify({"data": [x.json for x in posts],
                                        "next_exists": next_exists
                                        }
                                       )
                }
    else:
        return front_all()


def default_cat_cookie():

    output=[]
    for cat in CATEGORIES:
        for subcat in cat.subcats:
            if subcat.visible:
                output.append(subcat.id)

    output += [0]
    return output

@app.route("/categories", methods=["GET"])
@auth_desired
def categories_select(v):
    return render_template(
        "categorylisting.html",
        v=v,
        categories=CATEGORIES
        )


@app.route("/all", methods=["GET"])
@app.route("/api/v1/all/listing", methods=["GET"])
@app.route("/inpage/all")
@auth_desired
@api("read")
def front_all(v):

    page = int(request.args.get("page") or 1)

    # prevent invalid paging
    page = max(page, 1)

    sort_method = request.args.get("sort", "hot")
    t = request.args.get('t', 'all')
    ignore_pinned = bool(request.args.get("ignore_pinned", False))


    cats=session.get("catids")
    new_cats=request.args.get('cats','')
    if not cats and not new_cats and not request.path.startswith('/api/'):
        return make_response(
            render_template(
                "categorylisting.html",
                v=v,
                categories=CATEGORIES
                )
            )


    if new_cats:
        #print('overwrite cats')
        new_cats=[int(x) for x in new_cats.split(',')]
        session['catids']=new_cats
        cats=new_cats
        session.modified=True

    #handle group cookie
    groups = request.args.get("groups")
    if groups:
        session['groupids']=[int(x) for x in groups.split(',')]
        session.modified=True

    #print(cats)

    ids = frontlist(sort=sort_method,
                    page=page,
                    nsfw=(v and v.over_18 and not v.filter_nsfw),
                    nsfl=(v and v.show_nsfl),
                    t=t,
                    v=v,
                    hide_offensive=(v and v.hide_offensive) or not v,
                    gt=int(request.args.get("utc_greater_than", 0)),
                    lt=int(request.args.get("utc_less_than", 0)),
                    filter_words=v.filter_words if v else [],
                    categories=[] if request.path.startswith("/api/") else cats
                    )

    # check existence of next page
    next_exists = (len(ids) == 26)
    ids = ids[0:25]

   # If page 1, check for sticky
    if page == 1 and not ignore_pinned:
        sticky = []
        sticky = g.db.query(Submission.id).filter_by(stickied=True).first()
        if sticky:
            ids = [sticky.id] + ids
    # check if ids exist
    posts = get_posts(ids, sort=sort_method, v=v)

    return {'html': lambda: render_template("home.html",
                                            v=v,
                                            listing=posts,
                                            next_exists=next_exists,
                                            sort_method=sort_method,
                                            time_filter=t,
                                            page=page,
                                            CATEGORIES=CATEGORIES
                                            ),
            'inpage': lambda: render_template("submission_listing.html",
                                              v=v,
                                              listing=posts
                                              ),
            'api': lambda: jsonify({"data": [x.json for x in posts],
                                    "next_exists": next_exists
                                    }
                                   )
            }


@cache.memoize(600)
def guild_ids(sort="subs", page=1, nsfw=False, cats=[]):
    # cutoff=int(time.time())-(60*60*24*30)

    guilds = g.db.query(Board).filter_by(is_banned=False)

    if not nsfw:
        guilds = guilds.filter_by(over_18=False)

    if cats:
        guilds=guilds.filter(Board.subcat.in_(tuple(cats)))

    if sort == "subs":
        guilds = guilds.order_by(Board.stored_subscriber_count.desc())
    elif sort == "new":
        guilds = guilds.order_by(Board.created_utc.desc())
    elif sort == "trending":
        guilds = guilds.order_by(Board.rank_trending.desc())

    else:
        abort(400)

    guilds = [x.id for x in guilds.offset(25 * (page - 1)).limit(26).all()]

    return guilds


@app.route("/browse", methods=["GET"])
@app.route("/api/v1/guilds")
@auth_desired
@api("read")
def browse_guilds(v):

    page = int(request.args.get("page", 1))

    # prevent invalid paging
    page = max(page, 1)

    sort_method = request.args.get("sort", "trending")

    # get list of ids
    ids = guild_ids(
        sort=sort_method, 
        page=page, 
        nsfw=(v and v.over_18),
        cats=request.args.get("cats").split(',') if request.args.get("cats") else None
        )

    # check existence of next page
    next_exists = (len(ids) == 26)
    ids = ids[0:25]

    # check if ids exist
    if ids:
        # assemble list of tuples
        i = 1
        tups = []
        for x in ids:
            tups.append((x, i))
            i += 1

        # tuple string
        tups = str(tups).lstrip("[").rstrip("]")

        # hit db for entries

        boards = g.db.query(
            Board).options(
            lazyload(
                '*'
            )).filter(
            Board.id.in_(ids)
            ).all()

        boards=sorted(boards, key=lambda x: ids.index(x.id))
    else:
        boards = []

    return {"html": lambda: render_template("boards.html",
                                            v=v,
                                            boards=boards,
                                            page=page,
                                            next_exists=next_exists,
                                            sort_method=sort_method
                                            ),
            "api": lambda: jsonify({"data": [board.json for board in boards]})
            }


@app.route('/mine', methods=["GET"])
@auth_required
def my_subs(v):

    kind = request.args.get("kind", "guilds")
    page = max(int(request.args.get("page", 1)), 1)

    if kind == "guilds":

        b = g.db.query(Board)
        contribs = g.db.query(ContributorRelationship.board_id).filter_by(user_id=v.id).subquery()
        m = g.db.query(ModRelationship.board_id).filter_by(user_id=v.id, accepted=True).subquery()
        s = g.db.query(Subscription.board_id).filter_by(user_id=v.id, is_active=True).subquery()

        content = b.filter(
            or_(
                Board.id.in_(contribs),
                Board.id.in_(m),
                Board.id.in_(s)
                )
            )
        content = content.order_by(Board.stored_subscriber_count.desc())

        content = [x for x in content.offset(25 * (page - 1)).limit(26)]
        next_exists = (len(content) == 26)
        content = content[0:25]

        return render_template("mine/boards.html",
                               v=v,
                               boards=content,
                               next_exists=next_exists,
                               page=page,
                               kind="guilds")

    elif kind == "users":

        u = g.db.query(User)
        follows = g.db.query(Follow).filter_by(user_id=v.id).subquery()

        content = u.join(follows,
                         User.id == follows.c.target_id,
                         isouter=False)

        content = content.order_by(User.follower_count.desc())

        content = [x for x in content.offset(25 * (page - 1)).limit(26)]
        next_exists = (len(content) == 26)
        content = content[0:25]

        return render_template("mine/users.html",
                               v=v,
                               users=content,
                               next_exists=next_exists,
                               page=page,
                               kind="users")

    else:
        abort(400)


@app.route("/random/post", methods=["GET"])
@auth_desired
def random_post(v):

    x = g.db.query(Submission).options(
        lazyload('board')).filter_by(
        is_banned=False,
        ).filter(Submission.deleted_utc == 0)

    now = int(time.time())
    cutoff = now - (60 * 60 * 24 * 180)
    x = x.filter(Submission.created_utc >= cutoff)

    if not (v and v.over_18):
        x = x.filter_by(over_18=False)

    if not (v and v.show_nsfl):
        x = x.filter_by(is_nsfl=False)

    if v and v.hide_offensive:
        x = x.filter_by(is_offensive=False)

    if v:
        bans = g.db.query(
            BanRelationship.board_id).filter_by(
            user_id=v.id).subquery()
        x = x.filter(Submission.board_id.notin_(bans))

    total = x.count()
    n = random.randint(0, total - 1)

    post = x.order_by(Submission.id.asc()).offset(n).limit(1).first()
    return redirect(post.permalink)


@app.route("/random/guild", methods=["GET"])
@auth_desired
def random_guild(v):

    x = g.db.query(Board).filter_by(
        is_banned=False,
        is_private=False,
        over_18=False,
        is_nsfl=False)

    if v:
        bans = g.db.query(BanRelationship.id).filter_by(user_id=v.id).all()
        x = x.filter(Board.id.notin_([i[0] for i in bans]))

    total = x.count()
    n = random.randint(0, total - 1)

    board = x.order_by(Board.id.asc()).offset(n).limit(1).first()

    return redirect(board.permalink)


@app.route("/random/comment", methods=["GET"])
@auth_desired
def random_comment(v):

    x = g.db.query(Comment).filter_by(is_banned=False,
                                      over_18=False,
                                      is_nsfl=False,
                                      is_offensive=False).filter(Comment.parent_submission.isnot(None))
    if v:
        bans = g.db.query(BanRelationship.id).filter_by(user_id=v.id).all()
        x = x.filter(Comment.board_id.notin_([i[0] for i in bans]))

    total = x.count()
    n = random.randint(0, total - 1)
    comment = x.order_by(Comment.id.asc()).offset(n).limit(1).first()

    return redirect(comment.permalink)


@app.route("/random/user", methods=["GET"])
@auth_desired
def random_user(v):
    x = g.db.query(User).filter(or_(User.is_banned == 0, and_(
        User.is_banned > 0, User.unban_utc < int(time.time()))))

    x = x.filter_by(is_private=False)

    total = x.count()
    n = random.randint(0, total - 1)

    user = x.offset(n).limit(1).first()

    return redirect(user.permalink)


@cache.memoize(600)
def comment_idlist(page=1, v=None, nsfw=False, **kwargs):

    posts = g.db.query(Submission).options(
        lazyload('*')).join(Submission.board)

    if not nsfw:
        posts = posts.filter_by(over_18=False)

    if v and not v.show_nsfl:
        posts = posts.filter_by(is_nsfl=False)

    if v and v.admin_level >= 4:
        pass
    elif v:
        m = g.db.query(ModRelationship.board_id).filter_by(
            user_id=v.id, invite_rescinded=False).subquery()
        c = g.db.query(
            ContributorRelationship.board_id).filter_by(
            user_id=v.id).subquery()

        posts = posts.filter(
            or_(
                Submission.author_id == v.id,
                Submission.post_public == True,
                Submission.board_id.in_(m),
                Submission.board_id.in_(c),
                Board.is_private == False
            )
        )
    else:
        posts = posts.filter(or_(Submission.post_public ==
                                 True, Board.is_private == False))

    posts = posts.subquery()

    comments = g.db.query(Comment).options(lazyload('*'))

    if v and v.hide_offensive:
        comments = comments.filter_by(is_offensive=False)

    if v and v.admin_level <= 3:
        # blocks
        blocking = g.db.query(
            UserBlock.target_id).filter_by(
            user_id=v.id).subquery()
        blocked = g.db.query(
            UserBlock.user_id).filter_by(
            target_id=v.id).subquery()

        comments = comments.filter(
            Comment.author_id.notin_(blocking),
            Comment.author_id.notin_(blocked)
        )

    if not v or not v.admin_level >= 3:
        comments = comments.filter_by(is_banned=False).filter(Comment.deleted_utc == 0)

    comments = comments.join(posts, Comment.parent_submission == posts.c.id)

    comments = comments.order_by(Comment.created_utc.desc()).offset(
        25 * (page - 1)).limit(26).all()

    return [x.id for x in comments]


@app.route("/all/comments", methods=["GET"])
@app.route("/api/v1/front/comments", methods=["GET"])
@auth_desired
@api("read")
def all_comments(v):

    page = int(request.args.get("page", 1))

    idlist = comment_idlist(v=v,
                            page=page,
                            nsfw=v and v.over_18,
                            nsfl=v and v.show_nsfl,
                            hide_offensive=v and v.hide_offensive)

    comments = get_comments(idlist, v=v)

    next_exists = len(idlist) == 26

    idlist = idlist[0:25]

    return {"html": lambda: render_template("home_comments.html",
                                            v=v,
                                            page=page,
                                            comments=comments,
                                            standalone=True,
                                            next_exists=next_exists),
            "api": lambda: jsonify({"data": [x.json for x in comments]})}


@app.route("/api/v1/categories", methods=["GET"])
@auth_desired
@api()
def categories(v):

    return make_response(
        jsonify(
            {"data":[x.json for x in CATEGORIES]}
            )
        )