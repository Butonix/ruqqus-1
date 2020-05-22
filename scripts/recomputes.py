from ruqqus.__main__ import db
from ruqqus.classes import *

from os import environ

import time
import threading

def recompute_comments(k, comments):
    print(f"starting comment thread{k}")

    for comment in comments.all():
        
        comment.score_disputed=comment.rank_fiery
        comment.score_hot=comment.rank_hot
        comment.score_top=comment.score

        db.add(comment)
        db.commit()

def recompute_posts(k, posts):

    print(f"starting post thread {k}")

    for post in posts.all():

        post.score_hot = post.rank_hot
        post.score_disputed=post.rank_fiery
        post.score_top=post.score
        post.score_activity=post.rank_activity

        db.add(post)
        db.commit()




def recompute():

    while True:

        db.begin(subtransactions=True)

        now=int(time.time())

        cutoff=now-(60860*24*180)

        print("Beginning thread forking")
        
        n_threads=int(environ.get('n_threads',2))
        

        thread_group=[]
        for i in range(n_threads):
            posts=db.query(Submission
                       ).filter_by(is_banned=False, is_deleted=False
                                   ).filter(Submission.created_utc>cutoff, text(f"(submissions.id+{i})%{n_threads}=0")
                                            ).order_by(Submission.id.desc()
                                                       )
            new_thread=threading.Thread(target=lambda:recompute_posts(i, posts))
            thread_group.append(new_thread)
            new_thread.start()

        
        

        i=0
        p=db.query(Submission
                   ).filter(Submission.created_utc>cutoff
                            ).subquery()
        
        for i in range(n_threads):
            comments=db.query(classes.comment.Comment
                             ).join(p,
                                    Comment.parent_submission==p.c.id
                                    ).filter(p.c.id != None,
                                             Comment.is_deleted==False,
                                             Comment.is_banned==False,
                                             text(f"(comments.id+{i}%{n_threads})=0")
                                             ):
            
            new_thread=threading.Thread(target=lambda:recompute_comments(i, comments))
            thread_group.append(new_thread)
            new_thread.start()

        print('threads started; master waiting')
        for thread in thread_group:
            thread.join()


recompute()
