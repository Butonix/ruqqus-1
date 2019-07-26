import yaml
from flask import *
from os import environ

config=yaml.safe_load(open(environ.get("banlist"), "w+", encoding="utf-16"))

def filter_post(post):

    if any([post.domain.endswith(x) for x in config["nosubmit"]]):
        return f"Domain {post.domain} isn't allowed."

    return False
