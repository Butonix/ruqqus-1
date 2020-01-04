from flask import render_template
import time
from sqlalchemy import *
from sqlalchemy.orm import relationship, deferred
from random import randint
import math

from ruqqus.helpers.base36 import *
from ruqqus.helpers.lazy import lazy
from ruqqus.__main__ import Base, db, cache
from .user import User
from .submission import Submission
from .votes import CommentVote
from .flags import CommentFlag

class Comment(Base):

    __tablename__="comments"

    id = Column(BigInteger, primary_key=True)
    author_id = Column(BigInteger, ForeignKey(User.id))
    body = Column(String(2000), default=None)
    parent_submission = Column(BigInteger, ForeignKey(Submission.id))
    parent_fullname = Column(BigInteger) #this column is foreignkeyed to comment(id) but we can't do that yet as "comment" class isn't yet defined
    created_utc = Column(BigInteger, default=0)
    edited_timestamp = Column(BigInteger, default=0)
    is_banned = Column(Boolean, default=False)
    body_html = Column(String)
    distinguish_level=Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    is_approved = Column(Integer, default=0)
    approved_utc=Column(Integer, default=0)

    #These are virtual properties handled as postgres functions server-side
    #There is no difference to SQLAlchemy, but they cannot be written to
    ups = Column(Integer, server_default=FetchedValue())
    downs=Column(Integer, server_default=FetchedValue())
    age=Column(Integer, server_default=FetchedValue())
    flags=relationship("CommentFlag", lazy="dynamic", backref="comment")
    flag_count=Column(Integer, server_default=FetchedValue())

    def __init__(self, *args, **kwargs):
                   

        if "created_utc" not in kwargs:
            kwargs["created_utc"]=int(time.time())
            
        for x in kwargs:
            if x not in ["ups","downs","score","rank_hot","rank_fiery","age","comment_count"]:
                self.__dict__[x]=kwargs[x]
                
    def __repr__(self):
        return f"<Comment(id={self.id})"
        

    @property
    @cache.memoize(timeout=60)
    def rank_hot(self):
        return (self.ups-self.down)/(((self.age+100000)/6)**(1/3))

    @property
    @cache.memoize(timeout=60)
    def rank_fiery(self):
        return (math.sqrt(self.ups * self.downs))/(((self.age+100000)/6)**(1/3))

    @property
    @cache.memoize(timeout=60)
    def score(self):
        return self.ups-self.downs
                

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
    @lazy
    def author(self):
        return db.query(User).filter_by(id=self.author_id).first()

    @property
    @lazy
    def post(self):

        return db.query(Submission).filter_by(id=self.parent_submission).first()
    
    @property
    @lazy
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
    def permalink(self):

        return f"/post/{self.post.base36id}/comment/{self.base36id}"

    @property
    @cache.memoize(timeout=60)
    def any_descendants_live(self):

        if self.replies==[]:
            return False

        if any([not x.is_banned and not x.is_deleted for x in self.replies]):
            return True

        else:
            return any([x.any_descendants_live for x in self.replies])
        

    def rendered_comment(self, v=None, render_replies=True, standalone=False, level=1):

        if self.is_banned or self.is_deleted:
            if v and v.admin_level>1:
                return render_template("single_comment.html", v=v, c=self, replies=self.replies, render_replies=render_replies, standalone=standalone, level=level)
                
            elif self.any_descendants_live:
                return render_template("single_comment_removed.html", c=self, replies=self.replies, render_replies=render_replies, standalone=standalone, level=level)
            else:
                return ""

        return render_template("single_comment.html", v=v, c=self, replies=self.replies, render_replies=render_replies, standalone=standalone, level=level)
    
    @property
    @cache.memoize(timeout=60)
    def score_fuzzed(self, k=0.01):
        real=self.score
        a=math.floor(real*(1-k))
        b=math.ceil(real*(1+k))
        return randint(a,b)
    
    @property
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

    @property
    def edited_string(self):

        if not self.edited_timestamp:
            return None

        age=int(time.time()-self.edited_timestamp)

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

    @property
    def active_flags(self):
        if self.is_approved:
            return 0
        else:
            return self.flag_count
        
class Notification(Base):

    __tablename__="notifications"

    id=Column(Integer, primary_key=True)
    user_id=Column(Integer, ForeignKey("users.id"))
    comment_id=Column(Integer, ForeignKey("comments.id"))
    read=Column(Boolean, default=False)

    #Server side computed values (copied from corresponding comment)
    created_utc=Column(Integer, server_default=FetchedValue())
    is_banned=Column(Boolean, server_default=FetchedValue())
    is_deleted=Column(Boolean, server_default=FetchedValue())

    def __repr__(self):

        return f"<Notification(id={self.id})"

    @property
    def comment(self):

        return db.query(Comment).filter_by(id=self.comment_id).first()
