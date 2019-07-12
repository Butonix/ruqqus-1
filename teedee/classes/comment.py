from flask import render_template
from teedee.helpers.base36 import *
from teedee.__main__ import Base, db
from time import strftime
from sqlalchemy import *
from .user import User
from .submission import Submission

class Comment(Base):

    __tablename__="Comments"

    id = Column(BigInteger, primary_key=True)
    author_id = Column(BigInteger, ForeignKey(User.id))
    body = Column(String(2000), default=None)
    parent_submission = Column(BigInteger, ForeignKey(Submission.id))
    parent_fullname = Column(BigInteger) #this column is foreignkeyed to comment(id) but we can't do that yet as "comment" class isn't yet defined
    created_utc = Column(BigInteger, default=0)
    is_banned = Column(Boolean, default=False)

    def __repr__(self):
        return "<Comment(id=%s, author_id=%s, body=%s, parent_submission=%s, " \
               "parent_comment=%s, created_utc=%s, is_banned=%s)>" \
               "" % (self.id, self.author_id, self.body, self.parent_submission,
                   self.parent_comment, self.created_utc, self.is_banned)
 
    
    @property
    def base36id(self):
        return base36encode(self.id)

    @property
    def fullname(self):
        return f"t3_{self.base36id}"

    @property
    def is_top_level(self):
        return self.parent_fullname.startswith("t2_")

    @property
    def author(self):
        return db.query(User).filter_by(id=author_id).first()
    
    @property
    def parent(self):

        if self.is_top_level:
            return db.query(Submission).filter_by(id=parent_submission).first()
        else:
            return db.query(Comment).filter_by(id=parent_comment).first()

    @property
    def children(self):

        return db.query(Comment).filter_by(parent_comment=self.id).all()

    @property
    def replies(self):

        if "replies" in self.__dict__:
            return self.__dict__["replies"]
        else:
            return db.query(Comment).filter_by(parent_fullname=self.fullname).all()

    @property
    def rendered_comment(self):

        return render_template("single_comment.html", c=self, replies=self.replies)
