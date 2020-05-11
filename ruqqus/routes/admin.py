from urllib.parse import urlparse
import time

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.get import *
from ruqqus.classes import *
from ruqqus.routes.admin_api import create_plot, user_stat_data
from flask import *
from ruqqus.__main__ import app, db



@app.route("/admin/flagged/posts", methods=["GET"])
@admin_level_required(3)
def flagged_posts(v):

    page=max(1, int(request.args.get("page", 1)))

    posts = db.query(Submission).filter_by(is_approved=0, is_banned=False).filter(Submission.flag_count>=1).order_by(Submission.flag_count.desc()).offset(25*(page-1)).limit(26)

    listing=[p for p in posts]
    next_exists=(len(listing)==26)
    listing=listing[0:25]

    return render_template("admin/flagged_posts.html", next_exists=next_exists, listing=listing, page=page, v=v)


@app.route("/admin/image_posts", methods=["GET"])
@admin_level_required(3)
@api
def image_posts_listing(v):

    page=int(request.args.get('page',1))

    posts=db.query(Submission).filter(Submission.url.ilike("https://i.ruqqus.com/post/%"
                                                                )
                                      ).order_by(Submission.id.desc()
                                                 ).offset(25*(page-1)
                                                          ).limit(26
                                                                  )
    
    posts=[x for x in posts]
    next_exists=(len(posts)==26)
    posts=posts[0:25]

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

    posts = db.query(Comment).filter_by(is_approved=0, is_banned=False).filter(Comment.flag_count>=1).order_by(Comment.flag_count.desc()).offset(25*(page-1)).limit(26)

    listing=[p for p in posts]
    next_exists=(len(listing)==26)
    listing=listing[0:25]

    return render_template("admin/flagged_comments.html", next_exists=next_exists, listing=listing, page=page, v=v)


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

    badge_types=db.query(BadgeDef).filter_by(kind=3).order_by(BadgeDef.rank).all()

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

    badge=db.query(BadgeDef).filter_by(id=badge_id).first()
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

    db.add(new_badge)
    db.commit()


    badge_types=db.query(BadgeDef).filter_by(kind=3).order_by(BadgeDef.rank).all()

    return redirect(user.permalink)
                 

@app.route("/admin/users", methods=["GET"])
@admin_level_required(2)
def users_list(v):

    page=int(request.args.get("page",1))

    users = db.query(User).filter_by(is_banned=0
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
