from os import environ
import secrets
from flask import *
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from flaskext.markdown import Markdown
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import *

from werkzeug.contrib.fixers import ProxyFix

_version = "0.5.0"

app = Flask(__name__,
            template_folder='./templates',
            static_folder='./static'
           )
app.wsgi_app = ProxyFix(app.wsgi_app, num_proxies=1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get("HEROKU_POSTGRESQL_TEAL_URL")
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

limit_url=environ.get("HEROKU_REDIS_PURPLE_URL", environ.get("HEROKU_REDIS_ORANGE_URL"))

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri=environ.get("HEROKU_REDIS_PURPLE_URL"),
    headers_enabled=True,
    strategy="fixed-window-elastic-expiry"
)

#setup db
_engine = create_engine(environ.get("HEROKU_POSTGRESQL_TEAL_URL"))
db = sessionmaker(bind=_engine)()
Base = declarative_base()

#import and bind all routing functions
import ruqqus.classes
from ruqqus.routes import *
import ruqqus.helpers.jinja2

if __name__ == "__main__":

    app.run(host="0.0.0.0", port="8000")

else:

    #enforce https
    @app.before_request
    def before_request():
        if request.url.startswith('http://') and "localhost" not in app.config["SERVER_NAME"]:
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)

        if not session.get("session_id"):
            session["session_id"]=secrets.token_hex(16)

        db.rollback()

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', "Origin, X-Requested-With, Content-Type, Accept, x-auth"
                             )
        return response

    
    
