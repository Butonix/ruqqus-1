from flask import *
from os import environ
import requests
from werkzeug.wrappers.response import Response as RespObj

from ruqqus.classes import *
from .get import *
from ruqqus.__main__ import Base, db, app


#Wrappers
def auth_desired(f):
    #decorator for any view that changes if user is logged in (most pages)

    def wrapper(*args, **kwargs):

        if "user_id" in session:
            v=db.query(User).filter_by(id=session["user_id"]).first()
            nonce=session.get("login_nonce",0)
            if nonce<v.login_nonce:
                v=None

        else:
            v=None
            
        resp=make_response( f(*args, v=v, **kwargs))
        if v:
            resp.headers.add("Cache-Control", "private")
            resp.headers.add("Access-Control-Allow-Origin",app.config["SERVER_NAME"])
        return resp

    wrapper.__name__=f.__name__
    return wrapper

def auth_required(f):
    #decorator for any view that requires login (ex. settings)

    def wrapper(*args, **kwargs):

        if "user_id" in session:
            v=db.query(User).filter_by(id=session["user_id"]).first()
            nonce=session.get("login_nonce",0)
            if nonce<v.login_nonce:
                abort(401)
            
            if not v:
                abort(401)

        else:
            abort(401)

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
            v=db.query(User).filter_by(id=session["user_id"]).first()
            nonce=session.get("login_nonce",0)
            if nonce<v.login_nonce:
                abort(401)
            
            if not v:
                abort(401)

            if v.is_banned:
                abort(403)
            
        else:
            abort(401)

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

        if v.is_banned:
            abort(403)

        return f(*args, board=board, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper

#this wrapper takes args and is a bit more complicated
def admin_level_required(x):

    def wrapper_maker(f):

        def wrapper(*args, **kwargs):


            if "user_id" in session:
                v=db.query(User).filter_by(id=session["user_id"]).first()
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

def api(f):

    def wrapper(*args, **kwargs):

        x=f(*args, **kwargs)

        if isinstance(x, RespObj):
            return x
        
        if request.path.startswith('/api/v1/'):
            return jsonify(x['api']())
        elif request.path.startswith('/inpage/'):
            return x['inpage']()
        else:
            return x['html']()

    wrapper.__name__=f.__name__
    return wrapper
