from ruqqus.__main__ import db_session
from ruqqus.classes import *

import time

db=db_session()

def recompute():

    x=0

    while True:

        print("beginning guild trend recompute")
        x+=1
        boards= db.query(Board).options(lazyload('*')).filter_by(is_banned=False).order_by(Board.rank_trending.desc())
        if x%10:
            boards=boards.limit(1000)

        i=0
        for board in boards.all():
            i+=1
            board.rank_trending=board.trending_rank
            board.stored_subscriber_count=board.subscriber_count
            db.add(board)

            if not i%100:
                db.commit()

        now=int(time.time())

        cutoff=now-(60860*24*180)

        print("Beginning post recompute")
        i=0
        page=1
        posts=True
        post_count=0
        while posts
            posts=db.query(Submission
                           ).options(lazyload('*')).filter_by(is_banned=False, is_deleted=False
                                       ).filter(Submission.created_utc>cutoff
                                                ).order_by(Submission.id.asc()
                                                           ).offset(1000*(page-1)).limit(1000).all()
            for post in posts:
                i+=1
                post_count+=1

                post.score_hot = post.rank_hot
                post.score_disputed=post.rank_fiery
                #post.score_top=post.score
                post.score_activity=post.rank_activity
                post.score_best=post.rank_best

                db.add(post)

            db.commit()
            page+=1
            print(f"re-scored {post_count} posts")
            

            #print(f"{i}/{total} - {post.base36id}")

        db.commit()

        print(f"Scored {i} posts. Beginning comment recompute")



        
        comments=True
        page=1
        comment_count=0
        while comments:
            comments=db.query(Comment
                             ).options(lazyload('*'), joinedload(Comment.post)).join(p,
                                    classes.comment.Comment.parent_submission==p.c.id
                                    ).filter(Submission.created_utc>cutoff,
                                             classes.comment.Comment.is_deleted==False,
                                             classes.comment.Comment.is_banned==False
                                             ).options(contains_eager(Comment.post)
                                             ).offset(1000*(page-1)).limit(1000).all():

            for comment in comments:

                comment_count+=1
            
            
                comment.score_disputed=comment.rank_fiery
                comment.score_hot=comment.rank_hot
                comment.score_top=comment.score

                db.add(comment)
            
            
            db.commit()

            print(f"re-scored {comment_count} comments")
        #time.sleep(60)


recompute()
