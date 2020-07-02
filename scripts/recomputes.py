from ruqqus.__main__ import db_session
from ruqqus import classes

import time

db=db_session()

def recompute():

    x=0

    while True:

        print("beginning guild trend recompute")
        x+=1
        boards= db.query(classes.boards.Board).filter_by(is_banned=False).order_by(classes.boards.Board.rank_trending.desc())
        if x%10:
            boards=boards.limit(1000)

        i=0
        for board in boards.all():
            i+=1
            board.rank_trending=board.trending_rank
            db.add(board)

            if not i%100:
                db.commit()
                time.sleep(0.5)

        now=int(time.time())

        cutoff=now-(60860*24*180)

        print("Beginning post recompute")
        i=0
        for post in db.query(classes.submission.Submission
                       ).filter_by(is_banned=False, is_deleted=False
                                   ).filter(classes.submission.Submission.created_utc>cutoff
                                            ).order_by(classes.submission.Submission.id.desc()
                                                       ).all():
            i+=1

            post.score_hot = post.rank_hot
            post.score_disputed=post.rank_fiery
            #post.score_top=post.score
            post.score_activity=post.rank_activity
            post.score_best=post.rank_best

            db.add(post)

            if not i%100:
                db.commit()
                time.sleep(0.5)
            

            #print(f"{i}/{total} - {post.base36id}")

        db.commit()

        print(f"Scored {i} posts. Beginning comment recompute")


        i=0
        p=db.query(classes.submission.Submission
                   ).filter(classes.submission.Submission.created_utc>cutoff
                            ).subquery()
        
        for comment in db.query(classes.comment.Comment
                             ).join(p,
                                    classes.comment.Comment.parent_submission==p.c.id
                                    ).filter(p.c.id != None,
                                             p.c.created_utc>cutoff,
                                             classes.comment.Comment.is_deleted==False,
                                             classes.comment.Comment.is_banned==False
                                             ).all():
            i+=1
            
            comment.score_disputed=comment.rank_fiery
            comment.score_hot=comment.rank_hot
            #comment.score_top=comment.score

            db.add(comment)
            if not i%100:
                db.commit()
                time.sleep(0.5)
            
        db.commit()

        print(f"Scored {i} comments. Sleeping 1min")

        #time.sleep(60)


recompute()
