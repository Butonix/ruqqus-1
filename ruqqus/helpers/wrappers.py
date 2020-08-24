from flask import *
from os import environ
import requests
from werkzeug.wrappers.response import Response as RespObj
import time

from ruqqus.classes import *
from .get import *
from ruqqus.__main__ import Base, app


#Wrappers
def auth_desired(f):
    #decorator for any view that changes if user is logged in (most pages)

    def wrapper(*args, **kwargs):

        if "user_id" in session:
            v=g.db.query(User).options(lazyload('*')).filter_by(id=session["user_id"]).first()
            nonce=session.get("login_nonce",0)
            if v and nonce<v.login_nonce:
                v=None

        else:
            v=None
        
        g.v=v

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

        if "user_id" in session:
            v=g.db.query(User).options(lazyload('*')).filter_by(id=session["user_id"]).first()
            nonce=session.get("login_nonce",0)
            if v and nonce<v.login_nonce:
                abort(401)
            
            if not v:
                abort(401)

        else:
            abort(401)

        g.v=v

        resp = make_response( f(*args, v=v, **kwargs))
        resp.headers.add("Cache-Control","private")
        resp.headers.add("Access-Control-Allow-Origin",app.config["SERVER_NAME"])
        return resp
    
    wrapper.__name__=f.__name__
    return wrapper

def is_not_banned(f):
    #decorator that enforces lack of ban

    def wrapper(*args, **kwargs):

        if "user_id" in session:
            v=g.db.query(User).options(lazyload('*')).filter_by(id=session["user_id"]).first()
            nonce=session.get("login_nonce",0)
            if v and nonce<v.login_nonce:
                abort(401)
            
            if not v:
                abort(401)

            if v.is_suspended:
                abort(403)
            
        else:
            abort(401)

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


            if "user_id" in session:
                v=g.db.query(User).options(lazyload('*')).filter_by(id=session["user_id"]).first()
                if not v:
                    abort(401)
                nonce=session.get("login_nonce",0)
                if nonce<v.login_nonce:
                    abort(401)
                
                if v.is_banned:
                    abort(403)

                if v.admin_level < x:
                    abort(403)

                #v.update_ip(request.remote_addr)
                    
            else:
                abort(401)

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

        submitted_key = request.values.get("formkey","none")
            
        if not submitted_key:
            print("no submitted key")
            abort(401)

        if not v.validate_formkey(submitted_key):
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

                #validate auth token
                token=request.headers.get("Authorization", "Bearer: ")
                try:
                    token=token.split()[1]
                except:
                    return jsonify({"error":"400 Bad Request. Authorization token not provided"}), 400
                
                client=g.db.query(ClientAuth).filter(
                    ClientAuth.access_token==token,
                    ClientAuth.access_token_expire_utc>int(time.time())
                    ).first()

                if not client:
                    return jsonify({"error":"401 Not Authorized. Invalid or Expired Token"}), 401

                #validate app associated with token
                if client.application.is_banned:
                    return jsonify({"error":f"403 Forbidden. The application `{client.application.app_name}` is suspended."}), 403

                #validate correct scopes for request
                for scope in scopes:
                    if not client.__dict__.get(f"scope_{scope}"):
                        return jsonify({"error":f"401 Not Authorized. Scope `{scope}` is required."}), 403
    
                if no_ban and client.user.is_banned and (client.user.unban_utc==0 or client.user.unban_utc>time.time()):
                    return jsonify({"error":f"403 Forbidden"}), 403

                result = f(*args, v=client.user, **kwargs)




                if isinstance(result, RespObj):
                    return result

                if request.path.startswith('/api/v1/'):
                    return jsonify(result['api']())
                else:
                    return result['html']()

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

