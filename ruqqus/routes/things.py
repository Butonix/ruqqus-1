from urllib.parse import urlparse
import mistletoe

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.filters import *
from ruqqus.classes import *
from flask import *
from ruqqus.__main__ import app, db


@app.route("/u/<username>", methods=["GET"])
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

@app.route("/post/<base36id>", methods=["GET"])
@auth_desired
def post_base36id(base36id, v=None):
    
    base10id = base36decode(base36id)
    
    try:
        post=db.query(Submission).filter_by(id=base10id).all()[0]
    except IndexError:
        abort(404)
        
    return post.rendered_page(v=v)


@app.route("/submit", methods=['POST'])
@is_not_banned
@validate_formkey
def submit_post(v):

    title=request.form.get("title","")
    url=request.form.get("url","")

    if len(title)<10:
        return render_template("submit.html", v=v, error="Please enter a better title.")
    
    x=urlparse(url)
    if not (x.scheme and x.netloc):
        return render_template("submit.html", v=v, error="Please enter a URL.")

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
    
    new_post=Submission(title=title,
                        url=url,
                        author_id=v.id
                        )

    #run through content filter
    x=filter_post(new_post)
    if x:
        return render_template("submit.html",v=v, error=x)
        

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
@auth_required
@validate_formkey
def api_comment(v):

    body=request.form.get("text")
    parent_fullname=request.form.get("parent_fullname")

    #sanitize
    body=request.form.get("body")
    body_md=mistletoe.markdown(body)
    body_html=sanitize(body_md, linkgen=True)

    #check existing
    existing=db.query(Comment).filter_by(author_id=v.id,
                                         body=body_md,
                                         parent_fullname=parent_fullname
                                         ).first()
    if existing:
        return redirect(existing.permalink)


    c=Comment(author_id=v.id,
              body=body_md,
              body_html=body_html)

    db.add(c)
    db.commit()

    return c.rendered_permalink
                                         
