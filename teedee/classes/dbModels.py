from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template
from random import seed, randint
from teedee.helpers.base36 import *
from teedee.__main__ import Base, db
from time import strftime
from sqlalchemy import *

class User(Base):

    __tablename__="users"
    id = Column(BigInteger, primary_key=True)
    username = Column(String, default=None)
    email = Column(String, default=None)
    passhash = Column(String, default=None)
    created_utc = Column(BigInteger, default=0)
    is_admin = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    ips = relationship('IPs', backref='users')
    username_verified = Column(Boolean, default=False)

    def hashPass(self, password):
        self.hash = generate_password_hash(password, method='pbkdf2:sha512', salt_length=8)
        return self.hash

    def verifyPass(self, password):
        return check_password_hash(self.hash, password)
    
    def rendered_userpage(self, v=None):

        if not self.is_banned:
            return render_template("userpage.html", u=self, v=v)
        else:
            return render_template("userpage_banned.html", u=self, v=v)
    
    def verify_username(self, username):
        
        #no reassignments allowed
        if self.username_verified:
            abort(403)
        
        #For use when verifying username with reddit
        #Set username. Randomize username of any other existing account with same
        try:
            existing = session.query(User).filter_by(username=username).all()[0]

            #No reassignments allowed
            if existing.username_verified:
                abort(403)
                
            # To avoid username collision on renaming any existing account, seed random with username
            seed(username)
            random_str = base36encode(randint(0,1000000000))
            existing.username=f"user_{random_str}"
            
            session.add(existing)
                                     
        except IndexError:
            pass
                                      
        self.username=username
        self.username_verified=True
        
        session.add(self)
        session.commit()

    @property
    def url(self):
        return f"/u/{self.username}"

    def __repr__(self):
        return f"<User(username={self.username})>"

    
class IPs(Base):
    __tablename__ = "Ips"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey(User.id), default=0)
    ip = Column(VARCHAR(40), default=None)

    def __repr__(self):
        return f"<Ips(id={self.id}, uid={self.user_id}, ip={self.ip})>"
                                      


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
                                      
    

class Comment(Base):

    __tablename__="Comments"

    id = Column(BigInteger, primary_key=True)
    author_id = Column(BigInteger, ForeignKey(User.id))
    body = Column(String(2000), default=None)
    parent_submission = Column(BigInteger, ForeignKey(Submission.id))
    parent_comment = Column(BigInteger) #this column is foreignkeyed to comment(id) but we can't do that yet as "comment" class isn't yet defined
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


