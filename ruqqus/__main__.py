import gevent.monkey
gevent.monkey.patch_all()

#import psycogreen.gevent
#psycogreen.gevent.patch_psycopg()

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
from sqlalchemy.orm import Session, sessionmaker, scoped_session
from sqlalchemy import *
from sqlalchemy.pool import QueuePool
import threading
import requests
import random

from redis import BlockingConnectionPool

from werkzeug.middleware.proxy_fix import ProxyFix


_version = "2.18.0"

app = Flask(__name__,
            template_folder='./templates',
            static_folder='./static'
           )
app.wsgi_app = ProxyFix(app.wsgi_app, num_proxies=2)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DATABASE_URL'] = environ.get("DATABASE_CONNECTION_POOL_URL", environ.get("DATABASE_URL"))

app.config['SQLALCHEMY_READ_URIS']=[
    environ.get("DATABASE_CONNECTION_POOL_READ_01_URL"),
    environ.get("DATABASE_CONNECTION_POOL_READ_02_URL"),
    environ.get("DATABASE_CONNECTION_POOL_READ_03_URL")
    ]

app.config['SECRET_KEY']=environ.get('MASTER_KEY')
app.config["SERVER_NAME"]=environ.get("domain", environ.get("SERVER_NAME", None))
app.config["SESSION_COOKIE_NAME"]="session_ruqqus"
app.config["VERSION"]=_version
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config["SESSION_COOKIE_SECURE"] = environ.get("SESSION_COOKIE_SECURE", "true").lower() != "false"
app.config["SESSION_COOKIE_SAMESITE"]="Lax"

app.config["PERMANENT_SESSION_LIFETIME"]=60*60*24*365
app.config["SESSION_REFRESH_EACH_REQUEST"]=False

app.jinja_env.cache = {}

app.config["UserAgent"]=f"Ruqqus webserver tools for Ruqqus v{_version} developed by Ruqqus LLC for ruqqus.com."

if "localhost" in app.config["SERVER_NAME"]:
    app.config["CACHE_TYPE"]="null"
else:
    app.config["CACHE_TYPE"]=environ.get("CACHE_TYPE", 'filesystem')

app.config["CACHE_DIR"]=environ.get("CACHE_DIR", "ruqquscache")

#captcha configs
app.config["HCAPTCHA_SITEKEY"]=environ.get("HCAPTCHA_SITEKEY")
app.config["HCAPTCHA_SECRET"]=environ.get("HCAPTCHA_SECRET")



#antispam configs
app.config["SPAM_SIMILARITY_THRESHOLD"]=float(environ.get("SPAM_SIMILARITY_THRESHOLD", 0.5))
app.config["SPAM_SIMILAR_COUNT_THRESHOLD"]=int(environ.get("SPAM_SIMILAR_COUNT_THRESHOLD", 5))
app.config["SPAM_URL_SIMILARITY_THRESHOLD"]=float(environ.get("SPAM_URL_SIMILARITY_THRESHOLD", 0.1))
    
#app.config["CACHE_REDIS_URL"]=environ.get("REDIS_URL")
#app.config["CACHE_DEFAULT_TIMEOUT"]=60
#app.config["CACHE_KEY_PREFIX"]="flask_caching_"

#app.config["REDIS_POOL_SIZE"]=int(environ.get("REDIS_POOL_SIZE", 30))

#redispool=BlockingConnectionPool(max_connections=app.config["REDIS_POOL_SIZE"])
#app.config["CACHE_OPTIONS"]={'connection_pool':redispool}


#setup env vars - convenience statement

for x in ["DATABASE_URL","SECRET_KEY"]:
    if not app.config.get(x):
        raise RuntimeError(f"The following environment variable must be defined: {x}")

        

Markdown(app)
cache=Cache(app)
Compress(app)


app.config["RATELIMIT_STORAGE_URL"]=environ.get("REDIS_URL", "memory://")
app.config["RATELIMIT_KEY_PREFIX"]="flask_limiting_"
app.config["RATELIMIT_ENABLED"]=bool(int(environ.get("RATELIMIT_ENABLED", True)))

def limiter_key_func():
    return request.remote_addr

limiter = Limiter(
    app,
    key_func=limiter_key_func,
    default_limits=["100/minute"],
    headers_enabled=True,
    strategy="fixed-window"
)

#setup db
pool_size=int(environ.get("PG_POOL_SIZE", 10))
engines={
    "leader":create_engine(app.config['DATABASE_URL'], pool_size=pool_size, pool_use_lifo=True) ,
    "followers":[create_engine(x, pool_size=pool_size, pool_use_lifo=True) for x in app.config['SQLALCHEMY_READ_URIS'] if x] if any(i for i in app.config['SQLALCHEMY_READ_URIS']) else [create_engine(app.config['DATABASE_URL'], pool_size=pool_size, pool_use_lifo=True)]
}


class RoutingSession(Session):
    def get_bind(self, mapper=None, clause=None):
        try:
            if self._flushing or request.method=="POST":
                return engines['leader']
            else:
                return random.choice(engines['followers'])
        except:
            if self._flushing:
                return engines['leader']
            else:
                return random.choice(engines['followers'])

db_session=scoped_session(sessionmaker(class_=RoutingSession))
#db_session=scoped_session(sessionmaker(bind=engines["leader"]))

Base = declarative_base()

#import and bind all routing functions
import ruqqus.classes
from ruqqus.routes import *
import ruqqus.helpers.jinja2


@app.before_first_request
def app_setup():
    #app.config["databases"]=scoped_session(sessionmaker(class_=RoutingSession))
    pass


IP_BAN_CACHE_TTL = int(environ.get("IP_BAN_CACHE_TTL", 3600))
UA_BAN_CACHE_TTL = int(environ.get("UA_BAN_CACHE_TTL", 3600))


@cache.memoize(IP_BAN_CACHE_TTL)
def is_ip_banned(remote_addr):
    """
    Given a remote address, returns whether or not user is banned
    """
    return bool(g.db.query(ruqqus.classes.IP).filter_by(addr=remote_addr).count())


@cache.memoize(UA_BAN_CACHE_TTL)
def get_useragent_ban_response(user_agent_str):
    """
    Given a user agent string, returns a tuple in the form of:
    (is_user_agent_banned, (insult, status_code))
    """
    result = g.db.query(ruqqus.classes.Agent).filter(ruqqus.classes.Agent.kwd.in_(user_agent_str.split())).first()
    if result:
        return True, (result.mock or "Follow the robots.txt, dumbass", result.status_code or 418)
    return False, (None, None)


#enforce https
@app.before_request
def before_request():

    g.db = db_session()

    session.permanent = True

    if is_ip_banned(request.remote_addr):
        return "", 403

    ua_banned, response_tuple = get_useragent_ban_response(request.headers.get("User-Agent", "NoAgent"))
    if ua_banned and request.path != "/robots.txt":
        return response_tuple

    if request.url.startswith("http://") and "localhost" not in app.config["SERVER_NAME"]:
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)

    if not session.get("session_id"):
        session["session_id"]=secrets.token_hex(16)

    #g.db.begin_nested()


def log_event(name, link):

    sleep(5)

    x=requests.get(link)

    if x.status_code != 200:
        return


    text=f'> **{name}**\r> {link}'



    url=os.environ.get("DISCORD_WEBHOOK")
    headers={"Content-Type":"application/json"}
    data={"username":"ruqqus",
          "content": text
          }

    x=requests.post(url, headers=headers, json=data)
    print(x.status_code)
    

@app.after_request
def after_request(response):

    try:
        g.db.commit()
    except:
        pass #g.db.close()

    response.headers.add('Access-Control-Allow-Headers',
                         "Origin, X-Requested-With, Content-Type, Accept, x-auth"
                         )
    response.headers.add("Cache-Control",
                         "maxage=600")
    response.headers.add("Strict-Transport-Security","max-age=31536000")
    response.headers.add("Referrer-Policy","same-origin")
    #response.headers.add("X-Content-Type-Options","nosniff")
    response.headers.add("Feature-Policy",
                         "geolocation 'none'; midi 'none'; notifications 'none'; push 'none'; sync-xhr 'none'; microphone 'none'; camera 'none'; magnetometer 'none'; gyroscope 'none'; speaker 'none'; vibrate 'none'; fullscreen 'none'; payment")
    if not request.path.startswith("/embed/"):
        response.headers.add("X-Frame-Options",
                         "deny")

    #signups - hit discord webhook
    if request.method=="POST" and response.status_code in [301, 302] and request.path=="/signup":
        link=f'https://{app.config["SERVER_NAME"]}/@{request.form.get("username")}'
        thread=threading.Thread(target=lambda:log_event(name="Account Signup", link=link))
        thread.start()

    g.db.close()

    return response

@app.route("/<path:path>", subdomain="www")
def www_redirect(path):

    return redirect(f"https://ruqqus.com/{path}")

# @app.teardown_appcontext
# def teardown(resp):

#     g.db.close()

