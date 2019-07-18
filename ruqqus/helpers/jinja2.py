import time

from ruqqus.__main__ import app, db
from ruqqus.classes import IP

@app.template_filter("users_here")
def users_here(x):

    now=time.time()

    cutoff=now-300

    return len(db.query(IP).filter_by(created_utc>=cutoff).all())
