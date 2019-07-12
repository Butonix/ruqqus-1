from urllib.parse import urlparse

from teedee.helpers.wrappers import *
from teedee.helpers.base36 import *
from teedee.helpers.sanitize import *
from teedee.classes import *
from flask import *
from teedee.__main__ import app, db


@app.route("/u/<username>", methods=["GET"])
@auth_desired
def u_username(username, v=None):
    
    #username is unique so at most this returns one result. Otherwise 404
    try:
        #case insensitive search

        result = db.query(User).filter(User.username.ilike(username)).all()[0]

        #check for wrong cases

        if username != result.username:
            return redirect(result.url)
        
    except IndexError:
        abort(404)
        
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

    new_post=Submission(title=title,
                        url=url,
                        author_id=v.id
                        )

    db.add(new_post)
    db.commit()

    return redirect(new_post.permalink)

@app.route("/ip/<addr>", methods=["GET"])
@admin_level_required(4)
def ip_address(addr, v):

    #Restricted to trust+safety ranks and above (admin level 4)

    user_ids=[]
    for uid in db.query("ips").filter_by(ip=addr).all():
        if uid not in user_ids:
            user_ids.append(uid)
            
    users=[db.query("User").filter_by(id=x).first() for x in user_ids]
    users.sort(key=lambda x: x.username)

    return render_template("ips.html", addr=addr, users=users)    
    
