from urllib.parse import urlparse

from teedee.helpers.wrappers import *
from teedee.helpers.base36 import *
from teedee.helpers.sanitize import *
from teedee.classes import *
from flask import *
from teedee.__main__ import app


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
    
    #not yet implemented
    #return post.rendered_webpage


@app.route("/submit", methods=['POST'])
@auth_required
@validate_formkey
def submit_post(v):

    title=request.form.get("title","")
    url=request.form.get("url","")

    if len(title)<10:
        return render_template("submit.html", error="Please enter a better title.")



    x=urlparse(url)
    if not (x.scheme and x.netloc):
        return render_template("submit.html", error="Please enter a URL.")

    #sanitize title
    
    title=CleanWithoutLinkgen(title)
