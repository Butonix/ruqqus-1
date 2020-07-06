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

names=[x.username for x in deleted_accounts]+[y.username for y in banned_accounts]

names_to_release=[]
names_to_hold=[]
print(f"{len(names)} account names are eligible")

for name in names:
    if any([x in name.lower() for x in protected_terms]):
        names_to_hold.append(name)
    else:
        names_to_release.append(name)

names_to_release.sort()
names_to_hold.sort(0)

print(f"{len(names_to_release)} names to release")
print(names_to_release)
print("")

print(f"{len(names_to_hold)} names to hold")
print(names_to_hold)