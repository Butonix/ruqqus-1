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
from ruqqus.classes import *
from flask import *
from ruqqus.__main__ import app, db, limiter
from werkzeug.contrib.atom import AtomFeed
from datetime import datetime


@app.route("/post/<p_id>/comment/<c_id>", methods=["GET"])
@auth_desired
def post_pid_comment_cid(p_id, c_id, v=None):

    c_id = base36decode(c_id)

    comment=db.query(Comment).filter_by(id=c_id).first()
    if not comment:
        abort(404)

    p_id = base36decode(p_id)
    
    post=db.query(Submission).filter_by(id=p_id).first()
    if not post:
        abort(404)

    if comment.parent_submission != p_id:
        abort(404)
        
    return post.rendered_page(v=v, comment=comment)

@app.route("/api/comment", methods=["POST"])
@limiter.limit("10/minute")
@is_not_banned
@validate_formkey
def api_comment(v):

    parent_submission=base36decode(request.form.get("submission"))
    parent_fullname=request.form.get("parent_fullname")

    #process and sanitize
    body=request.form.get("body","")
    with UserRenderer() as renderer:
        body_md=renderer.render(mistletoe.Document(body))
    body_html=sanitize(body_md, linkgen=True)

    #Run safety filter
    ban=filter_comment_html(body_html)

    if ban:
        abort(422)

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
    mentions=soup.find_all("a", href=re.compile("/u/(\w+)"), limit=3)
    for mention in mentions:
        username=mention["href"].split("/u/")[1]
        user=db.query(User).filter_by(username=username).first()
        if user:
            notify_users.add(user.id)


    for id in notify_users:
        n=Notification(comment_id=c.id,
                       user_id=id)
        db.add(n)
    db.commit()
                           

    #create auto upvote
    vote=CommentVote(user_id=v.id,
                     comment_id=c.id,
                     vote_type=1
                     )

    db.add(vote)
    db.commit()

    return redirect(f"{c.post.permalink}#comment-{c.base36id}")


@app.route("/edit_comment", methods=["POST"])
@is_not_banned
@validate_formkey
def edit_comment(v):

    comment_id = request.form.get("id")
    body = request.form.get("comment", "")
    with UserRenderer() as renderer:
        body_md=renderer.render(mistletoe.Document(body))
    body_html = sanitize(body_md, linkgen=True)

    c = db.query(Comment).filter_by(id=base36decode(comment_id)).first()

    if not c:
        abort(404)

    if not c.author_id == v.id:
        abort(403)

    if c.is_banned or c.is_deleted:
        abort(403)

    c.body=body
    c.body_html=body_html
    c.edited_timestamp = time.time()

    db.add(c)
    db.commit()

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
