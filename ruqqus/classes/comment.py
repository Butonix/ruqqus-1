from flask import render_template
import time
from sqlalchemy import *
from sqlalchemy.orm import relationship

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
    votes = relationship("CommentVote")

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
    def parent(self):

        if self.is_top_level:
            return db.query(Submission).filter_by(id=parent_submission).first()
        else:
            return db.query(Comment).filter_by(id=parent_comment).first()

    @property
    @_lazy
    def children(self):

        return db.query(Comment).filter_by(parent_comment=self.id).all()

    @property
    @_lazy
    def replies(self):

        if "replies" in self.__dict__:
            return self.__dict__["replies"]
        else:
            return db.query(Comment).filter_by(parent_fullname=self.fullname).all()

    @property
    def rendered_comment(self):

        if self.is_banned:
            if self.replies:
                return render_template("single_comment_banned.html", c=self, replies=self.replies)
            else:
                return ""

        return render_template("single_comment.html", c=self, replies=self.replies)
    
    @property
    @_lazy
    def ups(self):
        return db.query(CommentVote).join(User).filter(CommentVote.comment_id==self.id).filter(CommentVote.vote_type==1).filter(User.is_banned==False).count()

    @property
    @_lazy
    def downs(self):
        return db.query(CommentVote).join(User).filter(CommentVote.comment_id==self.id).filter(CommentVote.vote_type==-1).filter(User.is_banned==False).count()

    @property
    @_lazy
    def score(self):
        return self.ups-self.downs
    
    @property
    @_lazy
    def score_fuzzed(self, k=0.01):
        real=self.score
        a=math.floor(real*(1-k))
        b=math.ceil(real*(1+k))
        return randint(a,b)        

    @property
    @_lazy
    def age(self):
        now=int(time.time())
        return now-self.created_utc

    @property
    @_lazy
    def rank_hot(self):
        return self.score/(((self.age+100000)/6)**(1/3))

    @property
    @_lazy
    def rank_controversial(self):
        return math.sqrt(self.ups*self.downs)/(((self.age+100000)/6)**(1/3))

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
