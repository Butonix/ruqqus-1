from flask import render_template, request
import time
from sqlalchemy import *
from sqlalchemy.orm import relationship
import math
from urllib.parse import urlparse
from random import randint

from ruqqus.helpers.base36 import *
from ruqqus.__main__ import Base, db
from .user import User
from .votes import Vote

class Submission(Base):

    __tablename__="submissions"

    id = Column(BigInteger, primary_key=True)
    author_id = Column(BigInteger, ForeignKey(User.id))
    title = Column(String(500), default=None)
    url = Column(String(500), default=None)
    created_utc = Column(BigInteger, default=0)
    is_banned = Column(Boolean, default=False)
    distinguish_level=Column(Integer, default=0)
    created_str=Column(String(255), default=None)
    stickied=Column(Boolean, default=False)
    comments=relationship("Comment", lazy="dynamic")

    def __init__(self, *args, **kwargs):

        if "created_utc" not in kwargs:
            kwargs["created_utc"]=int(time.time())
            kwargs["created_str"]=time.strftime("%I:%M %p on %d %b %Y", time.gmtime(kwargs["created_utc"]))
        
        super().__init__(*args, **kwargs)


    def __repr__(self):
        return f"<Submission(id={self.id})>"

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
    def votes(self):

        return db.query(Vote).join(User).filter(Vote.submission_id==self.id).filter(User.is_banned==False).all()
    
    @property
    @_lazy
    def base36id(self):
        return base36encode(self.id)

    @property
    @_lazy
    def fullname(self):
        return f"t2_{self.base36id}"

    @property
    @_lazy
    def permalink(self):
        return f"/post/{self.base36id}"
                                      
    def rendered_page(self, v=None):

        #check for banned
        if self.is_banned:
            return render_template("submission_banned.html", v=v, p=self)

        #load and tree comments
        if "replies" not in self.__dict__:
            self.tree_comments()

        #return template
        return render_template("submission.html", v=v, p=self, sort_type=request.args.get("sort","Hot").capitalize())

    @property
    @_lazy
    def author(self):
        if self.author_id==0:
            return None
        else:
            return db.query(User).filter_by(id=self.author_id).first()

    @property
    @_lazy
    def domain(self):
        return urlparse(self.url).netloc
        
    @property
    @_lazy
    def ups(self):
        return db.query(Vote).join(User).filter(Vote.submission_id==self.id).filter(Vote.vote_type==1).filter(User.is_banned==False).count()

    @property
    @_lazy
    def downs(self):
        return db.query(Vote).join(User).filter(Vote.submission_id==self.id).filter(Vote.vote_type==-1).filter(User.is_banned==False).count()

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
    def comment_count(self):
        return len(self.comments)

    def tree_comments(self):

        #list comments without re-querying db each time
        comments=[c for c in self.comments]

        #get sort type
        sort_type = request.args.get("sort","hot")

        #this is done in an ugly way in order to reduce computation time for larger comment sets
        self.replies=[]
        i=len(comments)-1
        
        while i>=0:
            if comments[i].parent_fullname==self.fullname:
                self.replies.append(comments[i])
                comments.pop(i)

            i-=1

        if sort_type=="hot":
            self.__dict__["replies"].sort(key=lambda x:x.rank_hot, reverse=True)
        elif sort_type=="top":
            self.__dict__["replies"].sort(key=lambda x:x.score, reverse=True)
        elif sort_type=="new":
            self.__dict__["replies"].sort(key=lambda x:x.created_utc, reverse=True)
        elif sort_type=="fiery":
            self.__dict__["replies"].sort(key=lambda x:x.rank_controversial, reverse=True)

        def tree_replies(thing):

            thing.__dict__["replies"]=[]
            i=len(comments)-1
        
            while i>=0:
                if comments[i].parent_fullname==thing.fullname:
                    thing.__dict__["replies"].append(comments[i])
                    comments.pop(i)

                i-=1

            if sort_type=="hot":
                thing.__dict__["replies"].sort(key=lambda x:x.rank_hot, reverse=True)
            elif sort_type=="top":
                thing.__dict__["replies"].sort(key=lambda x:x.score, reverse=True)
            elif sort_type=="new":
                thing.__dict__["replies"].sort(key=lambda x:x.created_utc, reverse=True)
            elif sort_type=="fiery":
                thing.__dict__["replies"].sort(key=lambda x:x.rank_controversial, reverse=True)

            for reply in thing.replies:
                tree_replies(reply)

        for reply in self.replies:
            tree_replies(reply)

        

        
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
        
