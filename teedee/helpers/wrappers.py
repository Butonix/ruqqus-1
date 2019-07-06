from flask import session
from teedee.__main__ import Base, db
from teedee.classes.dbModels import *

#Wrappers
def auth_desired(f):
    #decorator for any view that changes if user is logged in (most pages)

    def wrapper(*args, **kwargs):

        if "user_id" in session:
            kwargs['v']=db.query(User).filter_by(id=session["user_id"]).all()[0]
            
        return f(*args, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper

def auth_required(f):
    #decorator for any view that requires login (ex. settings)

    def wrapper(*args, **kwargs):

        if "user_id" in session:
            v=db.query(User).filter_by(id=session["user_id"]).all()
            if not v:
                abort(401)
            if args:
                args=tuple(list(args).append(v))
            else:
                args=(v,)
        else:
            abort(401)

        return f(*args, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper

def admin_required(f):
    #decorator for any api that requires admin perms

    def wrapper(*args, **kwargs):

        if "user_id" in session:
            v=db.query(User).filter_by(id=session["user_id"]).all()[0]
            if not v.is_admin:
                abort(403)

            if args:
                args=tuple(list(args).append(v))
            else:
                args=(v,)
            
        else:
            abort(401)

        return f(*args, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper
