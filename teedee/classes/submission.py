from flask import render_template
import time
from sqlalchemy import *
from sqlalchemy.orm import relationship
import math
from urllib.parse import urlparse
from random import randint

from teedee.helpers.base36 import *
from teedee.__main__ import Base, db
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
    votes=relationship("Vote")

    def __init__(self, *args, **kwargs):

        if "created_utc" not in kwargs:
            kwargs["created_utc"]=int(time.time())
            kwargs["created_str"]=time.strftime("%I:%M %p on %d %b %Y", time.gmtime(kwargs["created_utc"]))

        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<Submission(id={self.id})>"
    
    @property
    def base36id(self):
        return base36encode(self.id)

    @property
    def permalink(self):
        return f"/post/{self.base36id}"
                                      
    def rendered_page(self, v=None):

        #step 1: load and tree comments
        #step 2: render
        if self.is_banned:
            return render_template("submission_banned.html", v=v, p=self)
        else:
            return render_template("submission.html", v=v, p=self)

    @property
    def author(self):
        if self.author_id==0:
            return None
        else:
            return db.query(User).filter_by(id=self.author_id).first()

    @property
    def domain(self):
        return urlparse(self.url).netloc
        
    @property
    def ups(self):
        return len([x for x in self.votes if x.vote_type==1])

    @property
    def downs(self):
        return len([x for x in self.votes if x.vote_type==-1])

    @property
    def score(self):
        return self.ups-self.downs
    
    @property
    def score_fuzzed(self, k=0.01):
        real=self.score
        a=math.floor(real*(1-k))
        b=math.ceil(real*(1+k))
        return randint(a,b)        

    @property
    def age(self):
        now=int(time.time())
        return now-self.created_utc

    @property
    def rank_hot(self):
        return self.score/(((self.age+100)/6)^(1/3))

    @property
    def rank_controversial(self):
        return math.sqrt(self.ups*self.downs)/math.log(self.age+2)
