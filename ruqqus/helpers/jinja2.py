import time
import json

from sqlalchemy import text

from ruqqus.classes.user import User
from ruqqus.__main__ import app, db, cache



@app.template_filter("total_users")
@cache.memoize(timeout=60)
def total_users(x):

    return db.query(User).filter_by(is_banned=0).count()


@app.template_filter("source_code")
@cache.memoize(timeout=60*60*24)
def source_code(file_name):

    return open("/app/"+file_name, mode="r+").read()

@app.template_filter("full_link")
def full_link(url):

    return f"https://{app.config['SERVER_NAME']}{url}"

@app.template_filter("js_str_escape")
def js_str_escape(s):
    
    return json.dumps(s)
