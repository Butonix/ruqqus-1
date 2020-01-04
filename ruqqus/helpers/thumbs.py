import requests
from os import environ
from urllib.parse import urlparse

from .get import *
from ruqqus.__main__ import db

def thumbnail_thread(post, can_show_thumbnail=False):

    #step 1: see if post is image

    print("thumbnail thread")

    if can_show_thumbnail:
        print("image post")
        x=requests.head(post.url)

        if x.headers["Content-Type"].split("/")[0]=="image":
            post.is_image=True
            db.add(post)
            db.commit()

            return

    else:
        post.save_thumb()
