from teedee.classes.dbModels import *
from os import environ
from flask import *
from helpers import *

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get("DATABASE_URL")

@app.route("/test")
def test():
    return "Hello Bros"

@app.route("/u/<username>", methods=["GET"])
def u_username(username):
    
    #username is unique so at most this returns one result. Otherwise 404
    try:
        result = db.query(User).filter_by(username=username).all()[0]
    except IndexError:
        abort(404)
        
    return result.rendered_userpage

@app.route("/post/<base36id>", methods=["GET"])
def post_base36id(base36id):
    
    base10id = base36decode(base36id)
    
    try:
        post=db.query(Submissions).filter_by(id=base10id).all()[0]
    except IndexError:
        abort 404
        
    return f"post {base36id} (id {base10id}) with title {post.title} found."
    
    #not yet implemented
    #return post.rendered_webpage
