from flask import *
from os import environ
import requests

from ruqqus.__main__ import Base, db
from ruqqus.classes import *


#Wrappers
def auth_desired(f):
    #decorator for any view that changes if user is logged in (most pages)

    def wrapper(*args, **kwargs):

        if "user_id" in session:
            v=db.query(User).filter_by(id=session["user_id"]).first()
            #if v:
                #v.update_ip(request.remote_addr)
        else:
            v=None
            
        return f(*args, v=v, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper

def auth_required(f):
    #decorator for any view that requires login (ex. settings)

    def wrapper(*args, **kwargs):

        if "user_id" in session:
            v=db.query(User).filter_by(id=session["user_id"]).first()
            
            if not v:
                abort(401)
            #v.update_ip(request.remote_addr)

        else:
            abort(401)

        return f(*args, v=v, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper

def is_not_banned(f):
    #decorator that enforces lack of ban

    def wrapper(*args, **kwargs):

        if "user_id" in session:
            v=db.query(User).filter_by(id=session["user_id"]).first()
            
            if not v:
                abort(401)

            #v.update_ip(request.remote_addr)

            if v.is_banned:
                abort(403)
            
        else:
            abort(401)

        return f(*args, v=v, **kwargs)

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
                
                if v.is_banned:
                    abort(403)

                if v.admin_level < x:
                    abort(403)

                #v.update_ip(request.remote_addr)
                    
            else:
                abort(401)

            response= f(*args, v=v, **kwargs)

            if isinstance(response, tuple):
                return response[0]
            else:
                return response

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
