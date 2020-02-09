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

@app.route("/cid/<cid>", methods=["GET"])
@admin_level_required(1)
def comment_cid(cid, v):

    comment=get_comment(cid)
    return redirect(comment.permalink)

@app.route("/post/<p_id>/comment/<c_id>", methods=["GET"])
@auth_desired
def post_pid_comment_cid(p_id, c_id, v=None):

    comment=get_comment(c_id)

    post=get_post(p_id)

    if comment.parent_submission != post.id:
        abort(404)

    if post.over_18 and not (v and v.over_18) and not session_over18(comment.board):
        t=int(time.time())
        return render_template("errors/nsfw.html",
                               v=v,
                               t=t,
                               lo_formkey=make_logged_out_formkey(t),
                               board=comment.board
                               )

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
@limiter.limit("10/minute")
@is_not_banned
@tos_agreed
@validate_formkey
def api_comment(v):

    parent_submission=base36decode(request.form.get("submission"))
    parent_fullname=request.form.get("parent_fullname")

    #process and sanitize
    body=request.form.get("body","")[0:2000]
    with CustomRenderer() as renderer:
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
    elif parent_fullname.startswith("t3"):
        parent=db.query(Comment).filter_by(id=parent_id).first()

    #No commenting on deleted/removed things
    if parent.is_banned or parent.is_deleted:
        abort(403)

    #check for ban state
    post = get_post(request.form.get("submission"))
    if not post.board.can_comment(v):
        abort(403)
        
    #create comment
    c=Comment(author_id=v.id,
              body=body,
              body_html=body_html,
              parent_submission=parent_submission,
              parent_fullname=parent_fullname,
              )

    db.add(c)
    db.commit()

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

    return redirect(f"{c.permalink}?context=1")


@app.route("/edit_comment/<cid>", methods=["POST"])
@is_not_banned
@validate_formkey
def edit_comment(cid, v):

    c = get_comment(cid)

    if not c.author_id == v.id:
        abort(403)

    if c.is_banned or c.is_deleted:
        abort(403)

    if c.board.has_ban(v):
        abort(403)
        
    body = request.form.get("body", "")
    with CustomRenderer() as renderer:
        body_md=renderer.render(mistletoe.Document(body))
    body_html = sanitize(body_md, linkgen=True)

    #Run safety filter
    bans=filter_comment_html(body_html)

    if bans:
        return render_template("comment_failed.html",
                               action=f"/edit_comment/{c.base36id}",
                               badlinks=[x.domain for x in bans],
                               body=body,
                               v=v
                               )

    c.body=body
    c.body_html=body_html
    c.edited_utc = int(time.time())

    db.add(c)
    db.commit()

    path=request.form.get("current_page","/")

    return redirect(f"{path}#comment-{c.base36id}")

@app.route("/delete/comment/<cid>", methods=["POST"])
@auth_required
@validate_formkey
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
def embed_comment_cid(cid, pid=None):

    comment=get_comment(cid)

    if not comment.parent:
        abort(403)

    if comment.is_banned or comment.is_deleted:
        return render_template("embeds/comment_removed.html", c=comment)

    return render_template("embeds/comment.html", c=comment)
