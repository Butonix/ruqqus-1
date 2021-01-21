from ruqqus.__main__ import db_session
from ruqqus.classes import *

import time
import daemon

db = db_session()


def recompute():

    x = 0

    while True:

        #print("beginning guild trend recompute")
        x += 1
        boards = db.query(Board).options(
            lazyload('*')).filter_by(is_banned=False).order_by(Board.rank_trending.desc())
        if x % 10:
            boards = boards.limit(1000)

        i = 0
        for board in boards.all():
            i += 1
            board.rank_trending = board.trending_rank
            board.stored_subscriber_count = board.subscriber_count
            db.add(board)

            if not i % 100:
                db.commit()

        now = int(time.time())

        cutoff = now - (60 * 60 * 24 * 180)
        cutoff_purge = now - (60 * 60 * 24 * 90)

        #print("Beginning post recompute")
        i = 0
        page = 1
        posts = True
        post_count = 0
        while posts:
            posts = db.query(Submission
                             ).options(lazyload('*')).filter_by(is_banned=False, deleted_utc=0
                                                                ).filter(Submission.created_utc > cutoff
                                                                         ).order_by(Submission.id.asc()
                                                                                    ).offset(100 * (page - 1)).limit(100).all()

            for post in posts:
                i += 1
                post_count += 1

                post.upvotes = post.ups
                post.downvotes = post.downs
                db.add(post)
                db.flush()

                post.score_hot = post.rank_hot
                post.score_disputed = post.rank_fiery
                # post.score_top=post.score
                post.score_activity = post.rank_activity
                post.score_best = post.rank_best

                db.add(post)

                comment_count = 0
                for comment in post._comments.filter_by(
                        is_banned=False, deleted_utc=0).all():

                    comment_count += 1

                    comment.upvotes = comment.ups
                    comment.downvotes = comment.downs
                    db.add(comment)
                    db.flush()

                    comment.score_disputed = comment.rank_fiery
                    comment.score_hot = comment.rank_hot
                    # comment.score_top=comment.score

                    db.add(comment)

            db.commit()

            page += 1
            #print(f"re-scored {post_count} posts")

            # #print(f"{i}/{total} - {post.base36id}")

        db.commit()

        for action in db.query(ModAction).filter(ModAction.created_utc<int(time.time())-60*60*24*90).all():
            db.delete(action)
        db.commit()

        x = 0

        #purge deleted comments older than 90 days

        purge_posts = db.query(Submission).filter(Submission.deleted_utc < cutoff_purge, Submission.purged_utc==0).all()
        for p in purge_posts:
            x += 1
            p.submission_aux.body = ""
            p.submission_aux.body_html = ""
            p.submission_aux.url = ""
            p.submission_aux.embed_url = ""
            p.meta_text=""
            p.meta_description=""
            p.creation_ip = ""
            p.creation_region=""
            p.purged_utc=int(time.time())
            p.is_pinned = False
            p.is_stickied = False
            db.add(p)

            if not x % 100:
                db.commit()

        db.commit()

        x = 0
        purge_comments = db.query(Comment).filter(Comment.deleted_utc < cutoff_purge, Comment.purged_utc==0).all()
        for c in purge_comments:
            c += 1
            c.comment_aux.body = ""
            c.comment_aux.body_html = ""
            c.creation_ip = ""
            c.creation_region=""
            c.purged_utc=int(time.time())
            c.is_pinned = False
            db.add(c)

            if not x % 100:
                db.commit()

        db.commit()



with daemon.DaemonContext():
    recompute()
