from flask import render_template, session
from time import time, strftime, gmtime
from sqlalchemy import *

from teedee.helpers.base36 import *
from teedee.__main__ import Base, db

class Vote(Base):

    __tablename__="votes"

    id=Column(Integer, primary_key=True)
    user_id=Column(Integer, ForeignKey("users.id"))
    is_up=Column(Boolean)
    submission_id=Column(Integer, ForeignKey("submissions.id"))
    comment_id=Column(Integer, ForeignKey("comments.id"))
    created_utc=Column(Integer, default=0)

    
    def __init__(self, *args, **kwargs):
        if "created_utc" not in kwargs:
            kwargs["created_utc"]=int(time())
            

    def change_to(self, x):

        """
        1 - upvote
        0 - novote
        -1 - downvote
        """

        new={1:True, 0:None, -1:False}[x]
        if new==self.is_up:
            return

        self.is_up=new
        self.created_utc=int(time())

        db.add(self)
        db.commit()
