from ruqqus.__main__ import *
from ruqqus.classes import *
import time

db=db_session()

protected_terms=[
    "ruqqus",
    "captain",
    "meta4",
    "gabe",
    "sublime",
    "slime"
]

protected_terms=[i.lower() for i in protected_terms]

now=(int)

deleted_accounts=db.query(User).filter_by(is_deleted=True)

print()

displayed_post_owners=db.query(Submission.author_id).filter_by(is_deleted=False, is_banned=False).distinct().subquery()
displayed_comment_owners=db.query(Comment.author_id).filter_by(is_deleted=False, is_banned=False).distinct().subquery()

banned_accounts=db.query(User).filter_by(unban_utc=0).filter(User.is_banned>0, User.id.notin_(displayed_post_owners), User.id.notin_(displayed_comment_owners))

accounts=[x for x in deleted_accounts]+[y for y in banned_accounts]

accounts_to_release=[]
accounts_to_hold=[]
print(f"{len(accounts)} account names are eligible")

for u in accounts:
    if any([x in u.username.lower() for x in protected_terms]):
        accounts_to_hold.append(u)
    else:
        accounts_to_release.append(u)

accounts_to_release.sort(key=lambda x:x.username)
accounts_to_hold.sort(key=lambda x:x.username)

print(f"{len(accounts_to_release)} names to release")
print(accounts_to_release)
print("")

print(f"{len(accounts_to_hold)} names to hold")
print(accounts_to_hold)
#for name in names_to_release: