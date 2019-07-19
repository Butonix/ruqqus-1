from flask import render_template, session
from time import time, strftime, gmtime
from sqlalchemy import *

from ruqqus.helpers.base36 import *
from ruqqus.__main__ import Base, db

class Vote(Base):

    __tablename__="votes"

    id=Column(Integer, primary_key=True)
    user_id=Column(Integer, ForeignKey("users.id"))
    vote_type=Column(Integer)
    submission_id=Column(Integer, ForeignKey("submissions.id"))
    created_utc=Column(Integer, default=0)

    
    def __init__(self, *args, **kwargs):
        
        if "created_utc" not in kwargs:
            kwargs["created_utc"]=int(time())

        super().__init__(*args, **kwargs)
            

    def change_to(self, x):

        """
        1 - upvote
        0 - novote
        -1 - downvote
        """
        if x in ["-1","0","1"]:
            x=int(x)
        elif x not in [-1, 0, 1]:
            abort(400)

        self.vote_type=x
        self.created_utc=int(time())

        db.add(self)
        db.commit()

class CommentVote(Base):

    __table__name="commentvotes"

    id=Column(Integer, primary_key=True)
    user_id=Column(Integer, ForeignKey("users.id"))
    vote_type=Column(Integer)
    comment_id=Column(Integer, ForeignKey("comments.id"))
    created_utc=Column(Integer, default=0)

    def __init__(self, *args, **kwargs):
        
        if "created_utc" not in kwargs:
            kwargs["created_utc"]=int(time())

        super().__init__(*args, **kwargs)
            

    def change_to(self, x):

        """
        1 - upvote
        0 - novote
        -1 - downvote
        """
        if x in ["-1","0","1"]:
            x=int(x)
        elif x not in [-1, 0, 1]:
            abort(400)

        self.vote_type=x
        self.created_utc=int(time())

        db.add(self)
        db.commit()
