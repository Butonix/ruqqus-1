from teedee.classes.dbModels import *
from os import environ
from flask import *
from teedee.helpers import *
from sqlalchemy import func

app = Flask(__name__,
            template_folder='./templates',
            static_folder='./static'
           )
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get("DATABASE_URL")
app.config['SECRET_KEY']=environ.get('Flask_secret_key')

#import routing functions that are offloaded to the other folder
from teedee.routes import *

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
        post=db.query(Submissions).filter_by(id=base10id).all()[0]
    except IndexError:
        abort(404)
        
    return post.rendered_page(v=v)
    
    #not yet implemented
    #return post.rendered_webpage
