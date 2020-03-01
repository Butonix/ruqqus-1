from flask import *
from ruqqus.__main__ import app, db, limiter
from werkzeug.contrib.atom import AtomFeed
from datetime import datetime
from ruqqus.classes.submission import *
from ruqqus.helpers import *

@app.route('/feeds/<sort>')
def feeds(sort=None):
    cutoff = int(time.time()) - (60 * 60 * 24) # 1 day

    posts = db.query(Submission).filter(Submission.created_utc>=cutoff,
                                        Submission.is_banned == False,
                                        Submission.is_deleted == False,
                                        Submission.stickied == False,
                                        Submission.is_public == True)

    if sort == "hot":
        posts = posts.order_by(text("submissions.rank_hot desc"))
    elif sort == "fiery":
        posts = posts.order_by(text("submissions.rank_fiery desc"))
    elif sort == "top":
        posts = posts.order_by(text("submissions.score desc"))


    feed = AtomFeed(title=f'Top 5 {sort} Posts from ruqqus',
                    feed_url=request.url, url=request.url_root)

    posts = posts.limit(5).all()

    for post in posts:
        feed.add(post.title, post.body_html,
                 content_type='html',
                 author=post.author.username,
                 url=f"https://ruqqus.com{post.permalink}",
                 updated=datetime.fromtimestamp(post.created_utc),
                 published=datetime.fromtimestamp(post.created_utc))
    return feed.get_response()