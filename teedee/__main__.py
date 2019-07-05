from teedee.classes.dbModels import *
from os import environ
from flask import *

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get("DATABASE_URL")

@app.route("/test")
def test():
    return "Hello Bros"

@app.route("/u/<username>")
def u_username(username):
    
    #username is unique so at most this returns one result. Otherwise 404
    try:
        result = next(session.query(User).filter_by(username=username))
    except StopIteration:
        abort(404)
        
    return result.rendered_userpage()
