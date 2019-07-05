from teedee.classes.dbModels import *
from os import environ
from flask import *
from teedee.helpers import *

app = Flask(__name__,
            template_folder='./templates',
            static_folder='./static'
           )
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get("DATABASE_URL")

@app.errorhandler(401)
def error_401(e):
    return render_template('401.html'), 401

@app.errorhandler(403)
def error_403(e):
    return render_template('403.html'), 403

@app.errorhandler(404)
def error_404(e):
    return render_template('404.html'), 404

@app.errorhandler(405)
def error_405(e):
    return render_template('405.html'), 405

@app.errorhandler(500)
def error_500(e):
    return render_template('500.html', e=e), 500

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
        abort(404)
        
    return f"post {base36id} (id {base10id}) with title {post.title} found."
    
    #not yet implemented
    #return post.rendered_webpage
