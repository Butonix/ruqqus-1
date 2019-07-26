import yaml
from flask import *
from os import environ

config=yaml.safe_load(open(environ.get("banlist"), "r+"))

def filter_post(url):

    domain=urlparse(self.url).netloc

    if any([domain.endswith(x) for x in config["nosubmit"]]):
        return f"Domain {post.domain} isn't allowed."

    return False
