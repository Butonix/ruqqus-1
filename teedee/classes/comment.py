from base import *
from sqlalchemy import *

class Comment(Base):

    __tablename__="submissions"

    id=Column(Integer, primary_key=True)
    author_id=Column(Integer)
    body=Column(String)
    parent_submission=Column(Integer)
    parent_comment=Column(Integer)
    created_utc=Column(Integer)
    is_banned=Column(Boolean)

    

