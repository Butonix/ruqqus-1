from urllib.parse import urlparse
import mistletoe
from sqlalchemy import func
from bs4 import BeautifulSoup

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.filters import *
from ruqqus.helpers.embed import *
from ruqqus.helpers.markdown import *
from ruqqus.helpers.get import *
from ruqqus.helpers.session import *
from ruqqus.classes import *
from flask import *
from ruqqus.__main__ import app, db, limiter
from werkzeug.contrib.atom import AtomFeed
from datetime import datetime

@app.route("/comment/<cid>", methods=["GET"])
def comment_cid(cid):

    comment=get_comment(cid)
    return redirect(comment.permalink)

@app.route("/post/<p_id>/comment/<c_id>", methods=["GET"])
@app.route("/api/v1/post/<p_id>/comment/<c_id>", methods=["GET"])
@auth_desired
@api
def post_pid_comment_cid(p_id, c_id, v=None):

    comment=get_comment(c_id)

    post=get_post(p_id)

    if comment.parent_submission != post.id:
        abort(404)

    board=post.board

    if board.is_banned and not (v and v.admin_level > 3):
        return {'html':lambda:render_template("board_banned.html",
                               v=v,
                               b=board),
                'api':lambda:{'error':f'+{board.name} is banned.'}
                }

    if post.over_18 and not (v and v.over_18) and not session_over18(comment.board):
        t=int(time.time())
        return {'html':lambda:render_template("errors/nsfw.html",
                               v=v,
                               t=t,
                               lo_formkey=make_logged_out_formkey(t),
                               board=comment.board
                               ),
                'api':lambda:{'error':f'This content is not suitable for some users and situations.'}
                }

    if post.is_nsfl and not (v and v.hide_nsfl) and not session_isnsfl(comment.board):
        t=int(time.time())
        return {'html':lambda:render_template("errors/nsfl.html",
                               v=v,
                               t=t,
                               lo_formkey=make_logged_out_formkey(t),
                               board=comment.board
                               ),
                'api':lambda:{'error':f'This content is not suitable for some users and situations.'}
                }


    #check guild ban
    board=post.board
    if board.is_banned and v.admin_level<3:
        return {'html':lambda:render_template("board_banned.html",
                               v=v,
                               b=board),
                'api':lambda:{'error':f'+{board.name} is banned.'}
        }

    #context improver
    context=int(request.args.get("context", 0))
    c=comment
    while context > 0 and not c.is_top_level:

        parent=c.parent
        parent.__dict__["replies"]=[c]

        c=parent
        context -=1
        
    return post.rendered_page(v=v, comment=c, comment_info=comment)

@app.route("/api/comment", methods=["POST"])
@limiter.limit("4/minute")
@is_not_banned
@tos_agreed
@validate_formkey
def api_comment(v):

    parent_submission=base36decode(request.form.get("submission"))
    parent_fullname=request.form.get("parent_fullname")

    #process and sanitize
    body=request.form.get("body","")[0:10000]

    with CustomRenderer(post_id=request.form.get("submission")) as renderer:
        body_md=renderer.render(mistletoe.Document(body))
    body_html=sanitize(body_md, linkgen=True)

    #Run safety filter
    bans=filter_comment_html(body_html)

    if bans:
        return render_template("comment_failed.html",
                               action="/api/comment",
                               parent_submission=request.form.get("submission"),
                               parent_fullname=request.form.get("parent_fullname"),
                               badlinks=[x.domain for x in bans],
                               body=body,
                               v=v
                               ), 422

    #check existing
    existing=db.query(Comment).filter_by(author_id=v.id,
                                         body=body,
                                         parent_fullname=parent_fullname,
                                         parent_submission=parent_submission
                                         ).first()
    if existing:
        return redirect(existing.permalink)

    #get parent item info
    parent_id=int(parent_fullname.split("_")[1], 36)
    if parent_fullname.startswith("t2"):
        parent=db.query(Submission).filter_by(id=parent_id).first()
        parent_comment_id=None
        level=1
    elif parent_fullname.startswith("t3"):
        parent=db.query(Comment).filter_by(id=parent_id).first()
        parent_comment_id=parent.id
        level=parent.level+1

    #No commenting on deleted/removed things
    if parent.is_banned or parent.is_deleted:
        abort(403)

    #check for ban state
    post = get_post(request.form.get("submission"))
    if post.is_archived or not post.board.can_comment(v):
        abort(403)

        
    #create comment
    c=Comment(author_id=v.id,
              body=body,
              body_html=body_html,
              parent_submission=parent_submission,
              parent_fullname=parent_fullname,
              parent_comment_id=parent_comment_id,
              level=level,
              author_name=v.username,
              over_18=post.over_18,
              is_nsfl=post.is_nsfl,
              is_op=(v.id==post.author_id)
              )

    db.add(c)
    db.commit()

    c.determine_offensive()

    notify_users=set()

    #queue up notification for parent author
    if parent.author.id != v.id:
        notify_users.add(parent.author.id)

    #queue up notifications for username mentions
    soup=BeautifulSoup(c.body_html, features="html.parser")
    mentions=soup.find_all("a", href=re.compile("^/@(\w+)"), limit=3)
    for mention in mentions:
        username=mention["href"].split("@")[1]
        user=db.query(User).filter_by(username=username).first()
        if user:
            notify_users.add(user.id)


    for x in notify_users:
        n=Notification(comment_id=c.id,
                       user_id=x)
        db.add(n)
    db.commit()
                           

    #create auto upvote
    vote=CommentVote(user_id=v.id,
                     comment_id=c.id,
                     vote_type=1
                     )

    db.add(vote)
    db.commit()

    #print(f"Content Event: @{v.username} comment {c.base36id}")

    return redirect(f"{c.permalink}?context=1")


@app.route("/edit_comment/<cid>", methods=["POST"])
@is_not_banned
@validate_formkey
@api
def edit_comment(cid, v):

    c = get_comment(cid)

    if not c.author_id == v.id:
        abort(403)

    if c.is_banned or c.is_deleted:
        abort(403)

    if c.board.has_ban(v):
        abort(403)
        
    body = request.form.get("body", "")[0:10000]
    with CustomRenderer() as renderer:
        body_md=renderer.render(mistletoe.Document(body))
    body_html = sanitize(body_md, linkgen=True)

    #Run safety filter
    bans=filter_comment_html(body_html)

    if bans:
        return {'html':lambda:render_template("comment_failed.html",
                               action=f"/edit_comment/{c.base36id}",
                               badlinks=[x.domain for x in bans],
                               body=body,
                               v=v
                               ),
                'api':lambda:{'error':f'A blacklist domain was used.'}
                }

    c.body=body
    c.body_html=body_html
    c.edited_utc = int(time.time())

    db.add(c)
    db.commit()

    c.determine_offensive()

    path=request.form.get("current_page","/")

    return redirect(f"{path}#comment-{c.base36id}")

@app.route("/delete/comment/<cid>", methods=["POST"])
@app.route("/api/v1/delete/comment/<cid>", methods=["POST"])
@auth_required
@validate_formkey
@api
def delete_comment(cid, v):

    c=db.query(Comment).filter_by(id=base36decode(cid)).first()

    if not c:
        abort(404)

    print(c.author_id)
    print(v.id)

    if not c.author_id==v.id:
        abort(403)

    c.is_deleted=True

    db.add(c)
    db.commit()

    return "", 204

@app.route('/feeds/<sort>')
def feeds(sort=None):
    cutoff = int(time.time()) - (60 * 60 * 24) # 1 day

    posts = db.query(Submission).filter(Submission.created_utc>=cutoff,
                                        Submission.is_banned == False,
                                        Submission.is_deleted == False,
                                        Submission.stickied == False)

    if sort == "hot":
        posts = posts.order_by(text("submissions.rank_hot desc"))
    elif sort == "fiery":
        posts = posts.order_by(text("submissions.rank_fiery desc"))
    elif sort == "top":
        posts = posts.order_by(text("submissions.score desc"))


    feed = AtomFeed(title=f'Top 5 {sort} Posts from ruqqus',
                    feed_url=request.url, url=request.url_root)

    posts = posts.limit(5).all()

    for post in posts:
        feed.add(post.title, post.body_html,
                 content_type='html',
                 author=post.author.username,
                 url=f"https://ruqqus.com{post.permalink}",
                 updated=datetime.fromtimestamp(post.created_utc),
                 published=datetime.fromtimestamp(post.created_utc))
    return feed.get_response()

@app.route("/embed/comment/<cid>", methods=["GET"])
@app.route("/embed/post/<pid>/comment/<cid>", methods=["GET"])
@app.route("/api/vi/embed/comment/<cid>", methods=["GET"])
@app.route("/api/vi/embed/post/<pid>/comment/<cid>", methods=["GET"])
@api
def embed_comment_cid(cid, pid=None):

    comment=get_comment(cid)

    if not comment.parent:
        abort(403)

    if comment.is_banned or comment.is_deleted:
        return {'html':lambda:render_template("embeds/comment_removed.html", c=comment),
                'api':lambda:{'error':f'Comment {cid} has been removed'}
               }

    if comment.board.is_banned:
        abort(410)

    return render_template("embeds/comment.html", c=comment)

