from os import environ
from flask import *
from flask_caching import Cache
from flaskext.markdown import Markdown
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import *

_version = "0.5.0"

app = Flask(__name__,
            template_folder='./templates',
            static_folder='./static'
           )
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get("DATABASE_URL")
app.config['SECRET_KEY']=environ.get('MASTER_KEY')
app.config["SERVER_NAME"]=environ.get("domain", None)
app.config["VERSION"]="0.1.0"

if "localhost" in app.config["SERVER_NAME"]:
    app.config["CACHE_TYPE"]="null"
else:
    app.config["CACHE_TYPE"]="redis"
    
app.config["CACHE_REDIS_URL"]=environ.get("REDIS_URL")
app.config["CACHE_DEFAULT_TIMEOUT"]=60

Markdown(app)
cache=Cache(app)

#setup db
_engine = create_engine(environ.get("DATABASE_URL"))
db = sessionmaker(bind=_engine)()
Base = declarative_base()

#import and bind all routing functions
import ruqqus.classes
from ruqqus.routes import *
import ruqqus.helpers.jinja2
#import ruqqus.helpers.db_prep

if __name__ == "__main__":

    app.run(host="0.0.0.0", port="8000")

else:

    #enforce https
    @app.before_request
    def before_request():
        if request.url.startswith('http://') and "localhost" not in app.config["SERVER_NAME"]:
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)

        db.rollback()

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', "Origin, X-Requested-With, Content-Type, Accept, x-auth"
                             )
        return response

    
    
