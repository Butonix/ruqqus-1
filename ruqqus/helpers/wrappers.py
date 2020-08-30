from flask import *
from os import environ
import requests
from werkzeug.wrappers.response import Response as RespObj
import time

from ruqqus.classes import *
from .get import *
from ruqqus.__main__ import Base, app

def get_logged_in_user():

    if request.path.startswith("/api/v1"):

        token=request.headers.get("Authorization")
        token=token.split()[1]

        client=g.db.query(ClientAuth).filter(
            ClientAuth.access_token==token,
            ClientAuth.access_token_expire_utc>int(time.time())
            ).first()

        x= (client.user, client) if client else (None, None)
        return x

    elif "user_id" in session:

        uid=session.get("user_id")
        nonce=session.get("login_nonce", 0)
        if not uid:
            return None, None
        v=g.db.query(User).options(lazyload('*')).filter_by(id=uid).first()
        if v and nonce<v.login_nonce:
            return None, None
        else:
            return v, None


    else:
        return None, None


#Wrappers
def auth_desired(f):
    #decorator for any view that changes if user is logged in (most pages)

    def wrapper(*args, **kwargs):

        v, c=get_logged_in_user()

        if c:
            kwargs["c"]=c

        resp=make_response( f(*args, v=v, **kwargs))
        if v:
            resp.headers.add("Cache-Control", "private")
            resp.headers.add("Access-Control-Allow-Origin",app.config["SERVER_NAME"])
        else:
            resp.headers.add("Cache-Control", "public")
        return resp

    wrapper.__name__=f.__name__
    return wrapper

def auth_required(f):
    #decorator for any view that requires login (ex. settings)

    def wrapper(*args, **kwargs):

        v, c=get_logged_in_user()

        if not v:
            abort(401)

        if c:
            kwargs["c"]=c


        g.v=v

        #an ugly hack to make api work
        resp = make_response( f(*args, v=v, **kwargs))

        resp.headers.add("Cache-Control","private")
        resp.headers.add("Access-Control-Allow-Origin",app.config["SERVER_NAME"])
        return resp
    
    wrapper.__name__=f.__name__
    return wrapper

def is_not_banned(f):
    #decorator that enforces lack of ban

    def wrapper(*args, **kwargs):

        v, c=get_logged_in_user()

        print(v, c)
            
        if not v:
            abort(401)

        if v.is_suspended:
            abort(403)

        if c:
            kwargs["c"]=c

        g.v=v

        resp=make_response(f(*args, v=v, **kwargs))
        resp.headers.add("Cache-Control","private")
        resp.headers.add("Access-Control-Allow-Origin",app.config["SERVER_NAME"])
        return resp

    wrapper.__name__=f.__name__
    return wrapper

#Require tos agreement
def tos_agreed(f):

    def wrapper(*args, **kwargs):

        v=kwargs['v']

        cutoff=int(environ.get("tos_cutoff",0))

        if v.tos_agreed_utc > cutoff:
            return f(*args, **kwargs)
        else:
            return redirect("/help/terms#agreebox")

    wrapper.__name__=f.__name__
    return wrapper

        

def is_guildmaster(f):
    #decorator that enforces guildmaster status
    #use under auth_required

    def wrapper(*args, **kwargs):

        v=kwargs["v"]
        boardname=kwargs.get("boardname")
        board_id=kwargs.get("bid")

        if boardname:
            board=get_guild(boardname)
        else:
            board=get_board(board_id)

        if not board.has_mod(v):
            abort(403)

        if v.is_banned and not v.unban_utc:
            abort(403)

        return f(*args, board=board, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper

#this wrapper takes args and is a bit more complicated
def admin_level_required(x):

    def wrapper_maker(f):

        def wrapper(*args, **kwargs):


            v, c = get_logged_in_user()

            if c:
                return jsonify({"error":"No admin api access"}), 403

            if not v:
                abort(401)
                
            if v.is_banned:
                abort(403)

            if v.admin_level < x:
                abort(403)


            g.v=v
            
            response= f(*args, v=v, **kwargs)

            if isinstance(response, tuple):
                resp=make_response(response[0])
            else:
                resp=make_response(response)
            
            resp.headers.add("Cache-Control","private")
            resp.headers.add("Access-Control-Allow-Origin",app.config["SERVER_NAME"])
            return resp

        wrapper.__name__=f.__name__
        return wrapper

    return wrapper_maker

def validate_formkey(f):

    """Always use @auth_required or @admin_level_required above @validate_form"""

    def wrapper(*args, v, **kwargs):

        if "c" not in kwargs:

            submitted_key = request.values.get("formkey","none")
                
            if not submitted_key:

                if request.path.startswith("/api/v1/") and request.headers.get("Authorization"):
                    pass
                else:
                    #print("no submitted key")
                    abort(401)

            elif not v.validate_formkey(submitted_key):
                abort(401)

        return f(*args, v=v, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper

def no_cors(f):

    """
    Decorator prevents content being iframe'd
    """

    def wrapper(*args, **kwargs):

        origin = request.headers.get("Origin",None)

        if origin and origin != "https://"+app.config["SERVER_NAME"]:

            return "This page may not be embedded in other webpages.", 403

        resp = make_response(f(*args, **kwargs))
        resp.headers.add("Access-Control-Allow-Origin",
                         app.config["SERVER_NAME"]
                         )

        return resp

    wrapper.__name__=f.__name__
    return wrapper

#wrapper for api-related things that discriminates between an api url
#and an html url for the same content
# f should return {'api':lambda:some_func(), 'html':lambda:other_func()}
def api(*scopes, no_ban=False):

    def wrapper_maker(f):

        def wrapper(*args, **kwargs):

            if request.path.startswith('/api/v1'):

                v=kwargs.get('v')
                client=kwargs.pop('c')

                if not v:
                    return jsonify({"error":"401 Not Authorized. Invalid or Expired Token"}), 401

                #validate app associated with token
                if client.application.is_banned:
                    return jsonify({"error":f"403 Forbidden. The application `{client.application.app_name}` is suspended."}), 403

                #validate correct scopes for request
                for scope in scopes:
                    if not client.__dict__.get(f"scope_{scope}"):
                        return jsonify({"error":f"401 Not Authorized. Scope `{scope}` is required."}), 403
    
                if (request.method=="POST" or no_ban) and client.user.is_suspended:
                    return jsonify({"error":f"403 Forbidden. The user account is suspended."}), 403

                result = f(*args, **kwargs)

                if isinstance(result, dict):
                    resp=result['api']()
                else:
                    resp=result

                resp=make_response(resp)

                resp.headers.add("Cache-Control","private")
                resp.headers.add("Access-Control-Allow-Origin",app.config["SERVER_NAME"])
                return resp

            else:

                result = f(*args, **kwargs)

                if isinstance(result, RespObj):
                    return result

                if request.path.startswith('/inpage/'):
                    return result['inpage']()
                else:
                    return result['html']()

        wrapper.__name__=f.__name__
        return wrapper

    return wrapper_maker

