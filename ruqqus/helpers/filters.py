import yaml
from flask import *
from os import environ
from urllib.parse import urlparse

config=yaml.safe_load(open(environ.get("banlist"), "r+"))

def filter_post(url):

    domain=urlparse(url).netloc

    if any([domain.endswith(x) for x in config["nosubmit"]]):
        return f"Domain {post.domain} isn't allowed."

    return False
