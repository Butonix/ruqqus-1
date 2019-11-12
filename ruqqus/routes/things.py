from urllib.parse import urlparse
import mistletoe
from sqlalchemy import func

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.filters import *
from ruqqus.helpers.embed import *
from ruqqus.classes import *
from flask import *
from ruqqus.__main__ import app, db

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

    reason=filter_post(url)
    if reason:
        return render_template("submit.html",v=v, error=reason)
        

    #sanitize title
    title=sanitize(title, linkgen=False)

    #check for duplicate
    dup = db.query(Submission).filter_by(title=title,
                                         author_id=v.id,
                                         url=url
                                         ).first()

    if dup:
        return redirect(dup.permalink)

    #now make new post

    body=request.form.get("body","")
    body_md=mistletoe.markdown(body)
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
                        embed_url=embed
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

@app.route("/ip/<addr>", methods=["GET"])
@admin_level_required(4)
def ip_address(addr, v):

    #Restricted to trust+safety ranks and above (admin level 4)

    user_ids=[]
    for ip in db.query(IP).filter_by(ip=addr).all():
        if ip.user_id not in user_ids:
            user_ids.append(ip.user_id)
            
    users=[db.query(User).filter_by(id=x).first() for x in user_ids]
    users.sort(key=lambda x: x.username)

    return render_template("ips.html", addr=addr, users=users, v=v)    
    
@app.route("/api/comment", methods=["POST"])
@is_not_banned
@validate_formkey
def api_comment(v):

    parent_submission=base36decode(request.form.get("submission"))
    parent_fullname=request.form.get("parent_fullname")

    #sanitize
    body=request.form.get("body","")
    body_md=mistletoe.markdown(body)
    body_html=sanitize(body_md, linkgen=True)

    #check existing
    existing=db.query(Comment).filter_by(author_id=v.id,
                                         body=body,
                                         parent_fullname=parent_fullname,
                                         parent_submission=parent_submission
                                         ).first()
    if existing:
        return redirect(existing.permalink)
    
    parent_id=int(parent_fullname.split("_")[1], 36)
    if parent_fullname.startswith("t2"):
        parent=db.query(Submission).filter_by(id=parent_id).first()
    elif parent_fullname.startswith("t3"):
        parent=db.query(Comment).filter_by(id=parent_id).first()

    if parent.is_banned:
        abort(403)


    c=Comment(author_id=v.id,
              body=body,
              body_html=body_html,
              parent_submission=parent_submission,
              parent_fullname=parent_fullname,
              parent_author_id=parent.author.id if parent.author.id != v.id else None
              )

    db.add(c)
    db.commit()

    vote=CommentVote(user_id=v.id,
                     comment_id=c.id,
                     vote_type=1
                     )

    db.add(vote)
    db.commit()

    return redirect(f"{c.post.permalink}#comment-{c.base36id}")
                                         


@app.route("/edit_comment", methods=["POST"])
@auth_required
@is_not_banned
@validate_formkey
def edit_comment(v):

    comment_id = request.form.get("id")
    body = request.form.get("comment", "")
    body_md = mistletoe.markdown(body)
    body_html = sanitize(body_md, linkgen=True)

    c = db.query(Comment).filter_by(id=comment_id,
                                    author_id=v.id).first()

    if not c:
        abort(404)

    c.body=body
    c.body_html=body_html
    c.edited_timestamp = time.time()

    db.add(c)
    db.commit()




