import time

from ruqqus.classes import *
from ruqqus.__main__ import app, db, cache

@app.template_filter("users_here")
def users_here(x):

    now=time.time()

    cutoff=now-300

    return 20

    return db.query(User).join(IP).filter(IP.created_utc>=cutoff).count()

@app.template_filter("total_users")
def total_users(x):

    return 10

    return db.query(User).filter_by(is_banned=False).all().count()
