from urllib.parse import urlparse
import time

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.alerts import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.get import *
from ruqqus.classes import *
from ruqqus.routes.admin_api import create_plot, user_stat_data
from flask import *
from ruqqus.__main__ import app



@app.route("/admin/flagged/posts", methods=["GET"])
@admin_level_required(3)
def flagged_posts(v):

    page=max(1, int(request.args.get("page", 1)))

    posts = g.db.query(Submission).filter_by(
        is_approved=0, 
        is_banned=False
        ).join(Submission.flags
        ).options(contains_eager(Submission.flags)
        ).order_by(Submission.id.desc()).offset(25*(page-1)).limit(26)

    listing=[p.id for p in posts]
    next_exists=(len(listing)==26)
    listing=listing[0:25]

    listing=get_posts(listing, v=v)

    return render_template("admin/flagged_posts.html", next_exists=next_exists, listing=listing, page=page, v=v)


@app.route("/admin/image_posts", methods=["GET"])
@admin_level_required(3)
@api("read")
def image_posts_listing(v):

    page=int(request.args.get('page',1))

    posts=g.db.query(Submission).filter_by(domain_ref=1).order_by(Submission.id.desc()
                                                 ).offset(25*(page-1)
                                                          ).limit(26)
    
    posts=[x.id for x in posts]
    next_exists=(len(posts)==26)
    posts=posts[0:25]

    posts=get_posts(posts, v=v)

    return {'html':lambda:render_template("admin/image_posts.html",
                                          v=v,
                                          listing=posts,
                                          next_exists=next_exists,
                                          page=page,
                                          sort_method="new"
                                          ),
            'api':lambda:[x.json for x in posts]
            }

    

@app.route("/admin/flagged/comments", methods=["GET"])
@admin_level_required(3)
def flagged_comments(v):

    page=max(1, int(request.args.get("page", 1)))

    posts = g.db.query(Comment
        ).filter_by(
            is_approved=0, 
            is_banned=False, 
            is_deleted=False
        ).join(Comment.flags).options(contains_eager(Comment.flags)
        ).order_by(Comment.id.desc()).offset(25*(page-1)).limit(26).all()

    listing=[p.id for p in posts]
    next_exists=(len(listing)==26)
    listing=listing[0:25]

    listing=get_comments(listing, v=v)

    return render_template("admin/flagged_comments.html",
        next_exists=next_exists, 
        listing=listing, 
        page=page, 
        v=v,
        standalone=True)


##@app.route("/admin/<path>", methods=["GET"])
##@admin_level_required(3):
##def admin_path(v):
##    try:
##        return render_template(safe_join("admin", path+".html"), v=v)
##    except jinja2.exceptions.TemplateNotFound:
##        abort(404)

@app.route("/admin", methods=["GET"])
@admin_level_required(3)
def admin_home(v):
    return render_template("admin/admin_home.html", v=v)


@app.route("/admin/badge_grant", methods=["GET"])
@admin_level_required(4)
def badge_grant_get(v):

    badge_types=g.db.query(BadgeDef).filter_by(kind=3).order_by(BadgeDef.rank).all()

    errors={"already_owned":"That user already has that badge.",
            "no_user":"That user doesn't exist."
            }

    return render_template("admin/badge_grant.html",
                           v=v,
                           badge_types=badge_types,
                           error=errors.get(request.args.get("error"),None) if request.args.get('error') else None,
                           msg="Badge successfully assigned" if request.args.get("msg") else None
                           )

@app.route("/badge_grant", methods=["POST"])
@admin_level_required(4)
@validate_formkey
def badge_grant_post(v):

    user=get_user(request.form.get("username"), graceful=True)
    if not user:
        return redirect("/badge_grant?error=no_user")

    badge_id=int(request.form.get("badge_id"))

    if user.has_badge(badge_id):
        return redirect("/badge_grant?error=already_owned")

    badge=g.db.query(BadgeDef).filter_by(id=badge_id).first()
    if badge.kind != 3:
        abort(403)

    new_badge=Badge(badge_id=badge_id,
                    user_id=user.id,
                    created_utc=int(time.time())
                    )

    desc=request.form.get("description")
    if desc:
        new_badge.description=desc

    
    url=request.form.get("url")
    if url:
        new_badge.url=url

    g.db.add(new_badge)

    g.db.commit()
    
    

    text=f"""
@{v.username} has given you the following profile badge:
\n\n![]({new_badge.path})
\n\n{new_badge.name}
"""
    
    send_notification(user, text)


    return redirect(user.permalink)
                 

@app.route("/admin/users", methods=["GET"])
@admin_level_required(2)
def users_list(v):

    page=int(request.args.get("page",1))

    users = g.db.query(User).filter_by(is_banned=0
                                     ).order_by(User.created_utc.desc()
                                                ).offset(25*(page-1)).limit(26)

    users=[x for x in users]

    next_exists = (len(users)==26)
    users=users[0:25]

    data = user_stat_data().get_json()



    return render_template("admin/new_users.html",
                           v=v,
                           users=users,
                           next_exists=next_exists,
                           page=page,
                           single_plot=data['single_plot'],
                           multi_plot=data['multi_plot']
                           )

@app.route("/admin/content_stats", methods=["GET"])
@admin_level_required(2)
def participation_stats(v):

    now=int(time.time())

    data={"valid_users":g.db.query(User).filter_by(is_deleted=False).filter(or_(User.is_banned==0, and_(User.is_banned>0, User.unban_utc<now))).count(),
          "private_users":g.db.query(User).filter_by(is_deleted=False, is_private=False).filter(User.is_banned>0, or_(User.unban_utc>now, User.unban_utc==0)).count(),
          "banned_users":g.db.query(User).filter(User.is_banned>0, or_(User.unban_utc>now, User.unban_utc==0)).count(),
          "deleted_users":g.db.query(User).filter_by(is_deleted=True).count(),
          "total_posts": g.db.query(Submission).count(),
          "posting_users": g.db.query(Submission.author_id).distinct().count(),
          "listed_posts": g.db.query(Submission).filter_by(is_banned=False, is_deleted=False).count(),
          "removed_posts":g.db.query(Submission).filter_by(is_banned=True).count(),
          "deleted_posts":g.db.query(Submission).filter_by(is_deleted=True).count(),
          "total_comments":g.db.query(Comment).count(),
          "commenting_users":g.db.query(Comment.author_id).distinct().count(),
          "removed_comments":g.db.query(Comment).filter_by(is_banned=True).count(),
          "deleted_comments":g.db.query(Comment).filter_by(is_deleted=True).count(),
          "total_guilds":g.db.query(Board).count(),
          "listed_guilds":g.db.query(Board).filter_by(is_banned=False, is_private=False).count(),
          "private_guilds":g.db.query(Board).filter_by(is_banned=False, is_private=True).count(),
          "banned_guilds":g.db.query(Board).filter_by(is_banned=True).count(),
          "post_votes":g.db.query(Vote).count(),
          "post_voting_users":g.db.query(Vote.user_id).distinct().count(),
          "comment_votes":g.db.query(CommentVote).count(),
          "comment_voting_users":g.db.query(CommentVote.user_id).distinct().count()
          }

    data={x:f"{data[x]:,}" for x in data}

    return render_template("admin/content_stats.html", v=v, data=data)


@app.route("/admin/vote_info", methods=["GET"])
@admin_level_required(4)
def admin_vote_info_get(v):

    if not request.args.get("link"):
        return render_template("admin/votes.html", v=v)

    thing=get_from_permalink(request.args.get("link"), v=v)

    if isinstance(thing, Submission):

        ups=g.db.query(Vote
            ).options(joinedload(Vote.user)
            ).filter_by(submission_id=thing.id, vote_type=1
            ).order_by(Vote.creation_ip.asc()
            ).all()

        downs=g.db.query(Vote
            ).options(joinedload(Vote.user)
            ).filter_by(submission_id=thing.id, vote_type=-1
            ).order_by(Vote.creation_ip.asc()
            ).all()

    elif isinstance(thing, Comment):

        ups=g.db.query(CommentVote
            ).options(joinedload(CommentVote.user)
            ).filter_by(comment_id=thing.id, vote_type=1
            ).order_by(CommentVote.creation_ip.asc()
            ).all()

        downs=g.db.query(CommentVote
            ).options(joinedload(CommentVote.user)
            ).filter_by(comment_id=thing.id, vote_type=-1
            ).order_by(CommentVote.creation_ip.asc()
            ).all()

    else:
        abort(400)


    return render_template("admin/votes.html",
        v=v,
        thing=thing,
        ups=ups,
        downs=downs,)

@app.route("/admin/alt_votes", methods=["GET"])
@admin_level_required(4)
def alt_votes_get(v):

    if not request.args.get("u1") or not request.args.get("u2"):
        return render_template("admin/alt_votes.html", v=v) 

    u1=request.args.get("u1")
    u2=request.args.get("u2")

    if not u1 or not u2:
        return redirect("/admin/alt_votes")

    u1=get_user(u1)
    u2=get_user(u2)

    u1_post_ups     = g.db.query(Vote.submission_id).filter_by(user_id=u1.id, vote_type=1).all()
    u1_post_downs   = g.db.query(Vote.submission_id).filter_by(user_id=u1.id, vote_type=-1).all()
    u1_comment_ups  = g.db.query(CommentVote.comment_id).filter_by(user_id=u1.id, vote_type=1).all()
    u1_comment_downs= g.db.query(CommentVote.comment_id).filter_by(user_id=u1.id, vote_type=-1).all()
    u2_post_ups     = g.db.query(Vote.submission_id).filter_by(user_id=u2.id, vote_type=1).all()
    u2_post_downs   = g.db.query(Vote.submission_id).filter_by(user_id=u2.id, vote_type=-1).all()
    u2_comment_ups  = g.db.query(CommentVote.comment_id).filter_by(user_id=u2.id, vote_type=1).all()
    u2_comment_downs= g.db.query(CommentVote.comment_id).filter_by(user_id=u2.id, vote_type=-1).all()

    data={}
    data['u1_only_post_ups']    = len([x for x in u1_post_ups if x not in u2_post_ups])
    data['u2_only_post_ups']    = len([x for x in u2_post_ups if x not in u1_post_ups])
    data['both_post_ups']       = len(list(set(u1_post_ups) & set(u2_post_ups)))

    data['u1_only_post_downs']  = len([x for x in u1_post_downs if x not in u2_post_downs])
    data['u2_only_post_downs']  = len([x for x in u2_post_downs if x not in u1_post_downs])
    data['both_post_downs']     = len(list(set(u1_post_downs) & set(u2_post_downs)))

    data['u1_only_comment_ups'] = len([x for x in u1_comment_ups if x not in u2_comment_ups])
    data['u2_only_comment_ups'] = len([x for x in u2_comment_ups if x not in u1_comment_ups])
    data['both_comment_ups']    = len(list(set(u1_comment_ups) & set(u2_comment_ups)))

    data['u1_only_comment_downs']    = len([x for x in u1_comment_downs if x not in u2_comment_downs])
    data['u2_only_comment_downs']    = len([x for x in u2_comment_downs if x not in u1_comment_downs])
    data['both_comment_downs']       = len(list(set(u1_comment_downs) & set(u2_comment_downs)))

    data['u1_post_ups_unique'] = 100 * data['u1_only_post_ups'] // len(u1_post_ups) if u1_post_ups else 0
    data['u2_post_ups_unique'] = 100 * data['u2_only_post_ups'] // len(u2_post_ups) if u2_post_ups else 0
    data['u1_post_downs_unique'] = 100 * data['u1_only_post_downs'] // len(u1_post_downs) if u1_post_downs else 0
    data['u2_post_downs_unique'] = 100 * data['u2_only_post_downs'] // len(u2_post_downs) if u2_post_downs else 0

    data['u1_comment_ups_unique'] = 100 * data['u1_only_comment_ups'] // len(u1_comment_ups) if u1_comment_ups else 0
    data['u2_comment_ups_unique'] = 100 * data['u2_only_comment_ups'] // len(u2_comment_ups) if u2_comment_ups else 0
    data['u1_comment_downs_unique'] = 100 * data['u1_only_comment_downs'] // len(u1_comment_downs) if u1_comment_downs else 0
    data['u2_comment_downs_unique'] = 100 * data['u2_only_comment_downs'] // len(u2_comment_downs) if u2_comment_downs else 0


    return render_template("admin/alt_votes.html",
        u1=u1, 
        u2=u2,
        v=v,
        data=data
        )


@app.route("/admin/link_accounts", methods=["POST"])
@admin_level_required(4)
@validate_formkey
def admin_link_accounts(v):

    u1=int(request.form.get("u1"))
    u2=int(request.form.get("u2"))

    new_alt=Alt(user1=u1, user2=u2)

    g.db.add(new_alt)

    return redirect(f"/admin/alt_votes?u1={g.db.query(User).get(u1).username}&u2={g.db.query(User).get(u2).username}")

@app.route("/admin/<pagename>", methods=["GET"])
@admin_level_required(3)
def admin_tools(v, pagename):
    return render_template(f"admin/{pagename}.html", v=v)