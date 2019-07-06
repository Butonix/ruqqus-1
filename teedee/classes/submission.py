from flask import render_template
from teedee.helpers.base36 import *
from teedee.__main__ import Base, db
from time import strftime
from sqlalchemy import *

class Submission(Base):

    __tablename__="Submissions"

    id = Column(BigInteger, primary_key=True)
    author_id = Column(BigInteger, ForeignKey(User.id))
    title = Column(String(500), default=None)
    url = Column(String(500), default=None)
    created_utc = Column(BigInteger, default=0)
    is_banned = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Submission(id={self.id})>"
    
    @property
    def base36id(self):
        return base36encode(self.id)

    @property
    def url(self):
        return f"/post/{self.base36id}"
                                      
    def rendered_page(self, v=None):

        #step 1: load and tree comments
        #step 2: render

        return "post found successfully, but this page isn't implemented yet"
