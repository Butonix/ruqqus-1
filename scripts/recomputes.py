from ruqqus.__main__ import db_session
from ruqqus.classes import *

import time
import daemon

db = db_session()

def print_(x):

    try:
        print(x)
    except OSError:
        pass


def recompute():

    cycle=0

    while True:

        cycle +=1
        print(f"cycle {cycle}")

        #purge deleted content older than 90 days

        now = int(time.time())
        cutoff_purge = now - (60 * 60 * 24 * 90)
        print_("beginning post purge")

        purge_posts = db.query(
            Submission
            ).filter(
            Submission.deleted_utc>0,
            Submission.deleted_utc < cutoff_purge, 
            Submission.purged_utc==0
            ).all()

        x=0
        for p in purge_posts:
            x += 1
            p.submission_aux.body = ""
            p.submission_aux.body_html = ""
            p.submission_aux.url = ""
            p.submission_aux.embed_url = ""
            p.submission_aux.meta_text=""
            p.submission_aux.meta_description=""
            p.creation_ip = ""
            p.creation_region=""
            p.purged_utc=int(time.time())
            p.is_pinned = False
            p.is_stickied = False
            p.domain_ref=None
            db.add(p)
            db.add(p.submission_aux)

            if not x % 100:
                print(f"purged {x} posts")
                db.commit()

        db.commit()
        print_(f"Done with post purge. Purged {x} posts")

        x = 0
        print_("beginning comment purge")
        purge_comments = db.query(
            Comment
            ).filter(
            Comment.deleted_utc>0,
            Comment.deleted_utc < cutoff_purge, 
            Comment.purged_utc==0,
            Comment.author_id != 1
            ).all()

        for c in purge_comments:
            x+=1
            c.comment_aux.body = ""
            c.comment_aux.body_html = ""
            c.creation_ip = ""
            c.creation_region=""
            c.purged_utc=int(time.time())
            c.is_pinned = False
            db.add(c)
            db.add(c.comment_aux)

            if not x % 100:
                print(f"purged {x} comments")
                db.commit()

        db.commit()
        print_(f"Done with comment purge. Purged {x} comments")

        print_("beginning guild trend recompute")
        boards = db.query(Board).options(
            lazyload('*')).filter_by(is_banned=False).order_by(Board.rank_trending.desc())
        if cycle % 10:
            print("top 1000 boards only")
            boards = boards.limit(1000)
        else:
            print("all boards")

        i = 0
        for board in boards.all():
            i += 1
            board.rank_trending = board.trending_rank
            board.stored_subscriber_count = board.subscriber_count
            db.add(board)

            if not i % 100:
                db.commit()

        print(f"Re-ranked {i} boards")


        cutoff = now - (60 * 60 * 24 * 180)

        print_("Beginning post recompute")
        page = 1
        post_count = 0
        posts_exist=True
        while i:
            posts = db.query(Submission
                ).options(
                    lazyload('*')
                ).filter_by(
                    is_banned=False,
                    deleted_utc=0
                ).filter(
                    Submission.created_utc > cutoff
                ).order_by(
                    Submission.id.asc()
                ).offset(
                    100 * (page - 1)
                ).limit(100).all()


            posts_exist=False
            for post in posts:
                posts_exist=True
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
            print_(f"re-scored {post_count} posts")

        print("Done with posts. Rescored {")

        db.commit()

        print("Deleting old mod actions")

        actions=db.query(ModAction).filter(ModAction.created_utc<int(time.time())-60*60*24*180)
        count=actions.count()
        actions.delete()
        db.commit()

        print(f"deleted {count} old mod actions")




with daemon.DaemonContext():
    recompute()

#recompute()