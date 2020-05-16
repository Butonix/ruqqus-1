from flask import *
import hmac
from .front import frontlist
from werkzeug.contrib.atom import AtomFeed
from datetime import datetime
from ruqqus.classes import *
from ruqqus.helpers.security import *
from ruqqus.helpers.jinja2 import full_link
from ruqqus.helpers.get import *

from ruqqus.__main__ import app, db, limiter

@app.route('/feeds/<sort>', methods=["GET"])
def feeds_public(sort=None):

    page=int(request.args.get("page", 1))
    t=request.args.get('t')
    
    posts=frontlist(sort=sort, page=page, t=t, v=None, hide_offensive=False, ids_only=False)


    feed = AtomFeed(title=f'Top 5 {sort} Posts from ruqqus',
                    feed_url=request.url, 
                    url=request.url_root
                    )

    for post in posts:
        feed.add(post.title, post.body_html,
                 content_type='html',
                 author=post.author.username,
                 url=full_link(post.permalink),
                 updated=datetime.fromtimestamp(post.created_utc),
                 published=datetime.fromtimestamp(post.created_utc),
                 links=[{'href':post.url}]
                 )

    return feed.get_response()

@app.route('/feeds/@<username>/<key>/<sort>', methods=["GET"])
def feeds_user(sort=None, username=None, key=None):
    if not username and key:
        return abort(501)

    user = get_user(username)
    if user.is_banned or user.is_deleted:
        abort(403)

    if not hmac.compare_digest(key, user.feedkey):
        ##invalid feedkey
        abort(403)

    page=int(request.args.get("page", 1))
    t=request.args.get('t')

    posts = user.idlist(sort=sort, page=page, t=t, ids_only=False)


    feed = AtomFeed(title=f'Top 5 {sort} Posts from ruqqus',
                    feed_url=request.url, url=request.url_root)

    for post in posts:

        feed.add(post.title, post.body_html,
                 content_type='html',
                 author=post.author.username,
                 url=full_link(post.permalink),
                 updated=datetime.fromtimestamp(post.created_utc),
                 published=datetime.fromtimestamp(post.created_utc),
                 links=[{'href':post.url}]
                 )

    return feed.get_response()