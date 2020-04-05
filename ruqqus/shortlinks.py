import gevent.monkey
gevent.monkey.patch_all()

from os import environ
import secrets
from flask import *
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_compress import Compress
from time import sleep

from flaskext.markdown import Markdown
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import *
import threading
import requests

from werkzeug.middleware.proxy_fix import ProxyFix

_version = "2.6.2"

app = Flask(__name__,
            template_folder='./templates',
            static_folder='./static',
           )
app.wsgi_app = ProxyFix(app.wsgi_app, num_proxies=2)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get("DATABASE_URL")
app.config['SECRET_KEY']=environ.get('MASTER_KEY')
app.config["SERVER_NAME"]=environ.get("domain", None)
app.config["SESSION_COOKIE_NAME"]="session_ruqqus"
app.config["VERSION"]=_version
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config["SESSION_COOKIE_SECURE"]=True
app.config["SESSION_COOKIE_SAMESITE"]="Lax"

app.config["PERMANENT_SESSION_LIFETIME"]=60*60*24*365
#app.config["SESSION_REFRESH_EACH_REQUEST"]=True

app.jinja_env.cache = {}

app.config["UserAgent"]="Ruqqus webserver ruqqus.com"

if "localhost" in app.config["SERVER_NAME"]:
    app.config["CACHE_TYPE"]="null"
else:
    app.config["CACHE_TYPE"]="redis"
    
app.config["CACHE_REDIS_URL"]=environ.get("REDIS_URL")
app.config["CACHE_DEFAULT_TIMEOUT"]=60

Markdown(app)
cache=Cache(app)
Compress(app)


limit_url=environ.get("HEROKU_REDIS_PURPLE_URL", environ.get("HEROKU_REDIS_AQUA_URL"))

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri=environ.get("HEROKU_REDIS_PURPLE_URL"),
    headers_enabled=True,
    strategy="fixed-window-elastic-expiry"
)

#setup db
_engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
db = sessionmaker(bind=_engine)()
Base = declarative_base()

#import and bind all routing functions
import ruqqus.classes
#from ruqqus.routes import *
import ruqqus.helpers.get import *

@app.route("/<pid>", host="ruqq.us")
@app.route("/<pid>/<cid>", host="ruqq.us")
def shortlink_redirect(pid, cid=None):

    if cid:

        comment=get_comment(cid)
        if comment.post.base36id != pid:
            abort(404)
        return redirect(comment.permalink)

    post=get_post(pid)
    return redirect(post.permalink)

@app.route("/", host="ruqq.us")
def shortlink_home():
    
    return redirect("https://ruqqus.com")
