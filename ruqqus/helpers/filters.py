import yaml
from flask import *

config=yaml.safe_load(open("/app/ruqqus/helpers/banned.txt", "r+"))

def filter_post(post):

    if any([post.domain.endswith(x) for x in config["nosubmit"]]):
        return f"Domain {post.domain} isn't allowed."

    return False

