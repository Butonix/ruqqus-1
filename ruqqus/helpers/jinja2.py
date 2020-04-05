import time
import json

from sqlalchemy import text

from ruqqus.classes.user import User
from .get import *
from ruqqus.__main__ import app, db, cache

@app.template_filter("source_code")
@cache.memoize(timeout=60*60*24)
def source_code(file_name):

    return open("/app/"+file_name, mode="r+").read()

@app.template_filter("full_link")
def full_link(url):

    return f"https://{app.config['SERVER_NAME']}{url}"
