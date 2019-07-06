from flask import session

#Wrappers
def auth_desired(f):
    #decorator for any view that changes if user is logged in (most pages)

    def wrapper(*args, **kwargs):

        if "user_id" in session:
            kwargs['v']=db.query(User).filter_by(id=Session["user_id"]).all()[0]
            
        return f(*args, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper

def auth_required(f):
    #decorator for any view that requires login (ex. settings)

    def wrapper(*args, **kwargs):

        if "user_id" in session:
            args.append(db.query(User).filter_by(id=Session["user_id"]).all()[0])
        else:
            abort(401)

        return f(*args, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper

def admin_required(f):
    #decorator for any api that requires admin perms

    def wrapper(*args, **kwargs):

        if "user_id" in session:
            args.append(db.query(User).filter_by(id=Session["user_id"]).all()[0])
            if not viewer.is_admin:
                abort(403)
            
        else:
            abort(401)

        return f(*args, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper
