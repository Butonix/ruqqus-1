from ruqqus.__main__ import *
from ruqqus.classes import *
import time

db=db_session()

now=(int)

deleted_accounts=db.query(User).filter_by(is_deleted=True)

displayed_post_owners=db.query(Submission.author_id).filter(is_deleted=False, is_banned=False).distinct().subquery()
displayed_comment_owners=db.query(Comment.author_id).filter(is_deleted=False, is_banned=False).distinct().subquery()

banned_accounts=db.query(User).filter_by(unban_utc=0).filter(User.is_banned>0, User.id.notin_(displayed_post_owners), User.id.notin_(displayed_comments_owners))

names=[x.username for x in deleted_accounts]+[y.username for y in banned_accounts]
print(names)