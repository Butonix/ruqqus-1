from flask import render_template
import time
from sqlalchemy import *
from sqlalchemy.orm import relationship
from random import randint
import math

from ruqqus.helpers.base36 import *
from ruqqus.__main__ import Base, db
from .user import User
from .submission import Submission
from .votes import CommentVote

class Comment(Base):

    __tablename__="comments"

    id = Column(BigInteger, primary_key=True)
    author_id = Column(BigInteger, ForeignKey(User.id))
    body = Column(String(2000), default=None)
    parent_submission = Column(BigInteger, ForeignKey(Submission.id))
    parent_fullname = Column(BigInteger) #this column is foreignkeyed to comment(id) but we can't do that yet as "comment" class isn't yet defined
    created_utc = Column(BigInteger, default=0)
    is_banned = Column(Boolean, default=False)
    body_html = Column(String)
    distinguish_level=Column(Integer, default=0)
    parent_author_id=Column(Integer, ForeignKey(User.id))
    read=Column(Boolean, default=False)

    #These are virtual properties handled as postgres functions server-side
    #There is no difference to SQLAlchemy, but they cannot be written to
    ups = Column(Integer, server_default=FetchedValue())
    downs=Column(Integer, server_default=FetchedValue())
    score=Column(Integer, server_default=FetchedValue())
    rank_hot=Column(Float, server_default=FetchedValue())
    rank_fiery=Column(Float, server_default=FetchedValue())
    age=Column(Integer, server_default=FetchedValue())

    def __init__(self, *args, **kwargs):

        if "created_utc" not in kwargs:
            kwargs["created_utc"]=int(time.time())
            
        for x in kwargs:
            if x not in ["ups","downs","score","rank_hot","rank_fiery","age","comment_count"]:
                self.__dict__[x]=kwargs[x]
                
    def __repr__(self):
        return f"<Comment(id={self.id})"
 
    def _lazy(f):

        def wrapper(self, *args, **kwargs):

            if "_lazy_dict" not in self.__dict__:
                self._lazy_dict={}

            if f.__name__ not in self._lazy_dict:
                self._lazy_dict[f.__name__]=f(self, *args, **kwargs)

            return self._lazy_dict[f.__name__]

        wrapper.__name__=f.__name__
        return wrapper

    @property
    @_lazy
    def base36id(self):
        return base36encode(self.id)

    @property
    @_lazy
    def fullname(self):
        return f"t3_{self.base36id}"

    @property
    @_lazy
    def is_top_level(self):
        return self.parent_fullname.startswith("t2_")

    @property
    @_lazy
    def author(self):
        return db.query(User).filter_by(id=self.author_id).first()

    @property
    @_lazy
    def post(self):

        return db.query(Submission).filter_by(id=self.parent_submission).first()
    
    @property
    def parent(self):

        if self.is_top_level:
            return db.query(Submission).filter_by(id=self.parent_submission).first()
        else:
            return db.query(Comment).filter_by(id=base36decode(self.parent_fullname.split(sep="_")[1])).first()

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
    @_lazy
    def permalink(self):

        return f"/post/{self.post.base36id}/comment/{self.base36id}"

    @property
    def any_descendants_live(self):

        if self.replies==[]:
            return False

        if any([not x.is_banned for x in self.replies]):
            return True

        else:
            return any([x.any_descendants_live for x in self.replies])
        

    def rendered_comment(self, v=None, render_replies=True):

        if self.is_banned:
            if v:
                if v.admin_level>1:
                    return render_template("single_comment.html", v=v, c=self, replies=self.replies)
                
            if self.any_descendants_live:
                return render_template("single_comment_banned.html", c=self, replies=self.replies)
            else:
                return ""

        return render_template("single_comment.html", v=v, c=self, replies=self.replies, render_replies=render_replies)
    
    @property
    @_lazy
    def score_fuzzed(self, k=0.01):
        real=self.score
        a=math.floor(real*(1-k))
        b=math.ceil(real*(1+k))
        return randint(a,b)
    
    @property
    @_lazy
    def age_string(self):

        age=self.age

        if age<60:
            return "just now"
        elif age<3600:
            minutes=int(age/60)
            return f"{minutes} minute{'s' if minutes>1 else ''} ago"
        elif age<86400:
            hours=int(age/3600)
            return f"{hours} hour{'s' if hours>1 else ''} ago"
        elif age<2592000:
            days=int(age/86400)
            return f"{days} day{'s' if days>1 else ''} ago"

        now=time.gmtime()
        ctd=time.gmtime(self.created_utc)
        months=now.tm_mon-ctd.tm_mon+12*(now.tm_year-ctd.tm_year)

        if months < 12:
            return f"{months} month{'s' if months>1 else ''} ago"
        else:
            years=now.tm_year-ctd.tm_year
            return f"{years} year{'s' if years>1 else ''} ago"
