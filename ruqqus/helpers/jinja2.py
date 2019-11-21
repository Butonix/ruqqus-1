import time

from sqlalchemy import text

from ruqqus.classes.user import User
from ruqqus.__main__ import app, db, cache



@app.template_filter("total_users")
@cache.memoize(timeout=60)
def total_users(x):

    return db.query(User).filter(text("ban_state>-1")).count()
