from flask import session
from teedee.__main__ import Base, db
from flask import *
from teedee.classes import *


#Wrappers
def auth_desired(f):
    #decorator for any view that changes if user is logged in (most pages)

    def wrapper(*args, **kwargs):

        if "user_id" in session:
            v=db.query(User).filter_by(id=session["user_id"]).all()[0]
        else:
            v=None
            
        return f(*args, v=v, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper

def auth_required(f):
    #decorator for any view that requires login (ex. settings)

    def wrapper(*args, **kwargs):

        if "user_id" in session:
            v=db.query(User).filter_by(id=session["user_id"]).all()
            if not v:
                abort(401)
            v=v[0]

        else:
            abort(401)

        return f(*args, v=v, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper

def is_not_banned(f):
    #decorator that enforces lack of ban

    def wrapper(*args, **kwargs):

        if "user_id" in session:
            v=db.query(User).filter_by(id=session["user_id"]).all()
            if not v:
                abort(401)
            v=v[0]
            
            if v.is_banned:
                abort(403)
            

        else:
            abort(401)

        return f(*args, v=v, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper
    

#this wrapper takes args and is a bit more complicated
class admin_level_required():
    def __init__(self, level):
        self.level=level

    def __call__(self, f):

        def wrapper(*args, **kwargs):
            
            if "user_id" in session:
                v=db.query(User).filter_by(id=session["user_id"]).all()
                if not v:
                    abort(401)
                v=v[0]
                
                if v.is_banned:
                    abort(403)

                if v.admin_level < self.level:
                    abort(403)
                    
            else:
                abort(401)

            return f(*args, v=v, **kwargs)

        wrapper.__name__=f.__name__
        return wrapper

def validate_formkey(f):

    """Always use @auth_required or @admin_level_required above @validate_form"""

    def wrapper(*args, v, **kwargs):

        submitted_key = request.form.get("formkey","none")

        if not v.validate_formkey(submitted_key):
            abort(401)

        return f(*args, v=v, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper
