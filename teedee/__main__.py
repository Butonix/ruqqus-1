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

#Errors
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

@app.route("/")
def test():
    return "Hello Bros"

#take care of static pages
@app.route('/static/<path:path>')
def static_service(path):
    return send_from_directory('./static', path)

@app.route("/u/<username>", methods=["GET"])
@auth_desired
def u_username(username, v=None):
    
    #username is unique so at most this returns one result. Otherwise 404
    try:
        result = db.query(User).filter_by(func.lower(User.username)==func.lower(username)).all()[0]

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
