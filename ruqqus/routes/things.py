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
from ruqqus.__main__ import app, db
from werkzeug.contrib.atom import AtomFeed
from datetime import datetime

BAN_REASONS=['',
            "URL shorteners are not permitted."
            ]

@app.route("/api/is_available/<name>", methods=["GET"])
def api_is_available(name):
    if db.query(User.username).filter(User.username.ilike(name)).count():
        return jsonify({name:False})
    else:
        return jsonify({name:True})


@app.route("/u/<username>", methods=["GET"])
@app.route("/u/<username>/posts", methods=["GET"])
@auth_desired
def u_username(username, v=None):
    
    #username is unique so at most this returns one result. Otherwise 404
    
    #case insensitive search

    result = db.query(User).filter(User.username.ilike(username)).first()

    if not result:
        abort(404)

    #check for wrong cases

    if username != result.username:
        return redirect(result.url)
        
    return result.rendered_userpage(v=v)

@app.route("/u/<username>/comments", methods=["GET"])
@auth_desired
def u_username_comments(username, v=None):
    
    #username is unique so at most this returns one result. Otherwise 404
    
    #case insensitive search

    result = db.query(User).filter(User.username.ilike(username)).first()

    if not result:
        abort(404)

    #check for wrong cases

    if username != result.username:
        return redirect(result.url)
        
    return result.rendered_comments_page(v=v)

@app.route("/post/<base36id>", methods=["GET"])
@auth_desired
def post_base36id(base36id, v=None):
    
    base10id = base36decode(base36id)
    
    post=db.query(Submission).filter_by(id=base10id).first()
    if not post:
        abort(404)
        
    return post.rendered_page(v=v)

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


@app.route("/submit", methods=['POST'])
@is_not_banned
@validate_formkey
def submit_post(v):

    title=request.form.get("title","")

    url=request.form.get("url","")

    if len(title)<10:
        return render_template("submit.html", v=v, error="Please enter a better title.")

    parsed_url=urlparse(url)
    if not (parsed_url.scheme and parsed_url.netloc) and not request.form.get("body"):
        return render_template("submit.html", v=v, error="Please enter a URL or some text.")

    #sanitize title
    title=sanitize(title, linkgen=False)

    #check for duplicate
    dup = db.query(Submission).filter_by(title=title,
                                         author_id=v.id,
                                         url=url
                                         ).first()

    if dup:
        return redirect(dup.permalink)

    
    #check for domain specific rules

    domain=urlparse(url).netloc

    ##all possible subdomains
    parts=domain.split(".")
    domains=[]
    for i in range(len(parts)):
        new_domain=parts[i]
        for j in range(i+1, len(parts)):
            new_domain+="."+parts[j]

        domains.append(new_domain)
        
    domain_obj=db.query(Domain).filter(Domain.domain.in_(domains)).first()

    if domain_obj:
        if not domain_obj.can_submit:
            return render_template("submit.html",v=v, error=BAN_REASONS[domain_obj.reason])


    #now make new post

    body=request.form.get("body","")

    with UserRenderer() as renderer:
        body_md=renderer.render(mistletoe.Document(body))
    body_html = sanitize(body_md, linkgen=True)

    #check for embeddable video
    domain=parsed_url.netloc
    embed=""
    if domain.endswith(("youtube.com","youtu.be")):
        embed=youtube_embed(url)

    
    
    new_post=Submission(title=title,
                        url=url,
                        author_id=v.id,
                        body=body,
                        body_html=body_html,
                        embed_url=embed,
                        domain_ref=domain_obj.id if domain_obj else None
                        )

    db.add(new_post)

    db.commit()

    vote=Vote(user_id=v.id,
              vote_type=1,
              submission_id=new_post.id
              )
    db.add(vote)
    db.commit()

    return redirect(new_post.permalink)
    
@app.route("/api/comment", methods=["POST"])
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
    soup=BeautifulSoup(c.body_html)
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

    if not c.author_id==v.id:
        abort(403)

    c.is_deleted=True

    db.add(c)
    db.commit()

    return redirect(c.permalink)


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