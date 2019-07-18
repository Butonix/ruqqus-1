import time

from ruqqus.__main__ import app, db
from ruqqus.classes import IP, User

@app.template_filter("users_here")
def users_here(x):

    now=time.time()

    cutoff=now-300

    return len(db.query(User).join(IP).filter(IP.created_utc>=cutoff).all())

@app.template_filter("total_users")
def total_users(x):

    return len(db.query(User).filter_by(is_banned=False).all())
