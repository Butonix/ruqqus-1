from base import *
from sqlalchemy import *

class Submission(Base):

    __tablename__="submissions"

    id=Column(Integer, primary_key=True)
    author_id=Column(Integer)
    title=Column(String)
    url=Column(String)
    created_utc=Column(Integer)
    is_banned=Column(Boolean)

    
