from flask import render_template
import time
from sqlalchemy import *
from .user import User
from urllib.parse import urlparse

from teedee.helpers.base36 import *
from teedee.__main__ import Base, db

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

    def __init__(self, *args, **kwargs):

        if "created_str" not in kwargs:
            kwargs["created_str"]=time.strftime("%I:%M %p on %d %b %Y", time.gmtime(self.created_utc))

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
        return len(db.query(Vote).filter_by(submission_id=self.id, is_up=True).all())

    @property
    def downs(self):
        return len(db.query(Vote).filter_by(submission_id=self.id, is_up=False).all())

    @property
    def score(self):
        return self.ups-self.downs

    @property
    def age(self):
        now=int(time.time())
        return now-self.created_utc()

    @property
    def rank_hot(self):
        return self.score/math.log(self.age+2)

    @property
    def rank_controversial(self):
        return math.sqrt(self.top*self.downs)/math.log(self.age+2)
