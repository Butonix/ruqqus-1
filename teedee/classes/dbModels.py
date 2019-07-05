from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import *
from os import environ
from flask import render_template



_engine = create_engine(environ.get("DATABASE_URL"))
db = sessionmaker(bind=_engine)()
Base = declarative_base()

class User(Base):

    __tablename__="Users"
    id = Column(BigInteger, primary_key=True)
    username = Column(String, default=None)
    email = Column(String, default=None)
    passhash = Column(String, default=None)
    created_utc = Column(BigInteger, default=0)
    is_admin = Column(Boolean, default=False)
    is_mod = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    ips = relationship('IPs', backref='users')


    def hashPass(self, password):
        self.hash = generate_password_hash(password, method='pbkdf2:sha512', salt_length=8)
        return self.hash

    def verifyPass(self, password):
        return check_password_hash(self.hash, password)
    
    def rendered_userpage(self):
        
        return render_template("userpage.html", user=self)

    def __repr__(self):
        return "<User(id=%s, username=%s, email=%s, passhash=%s, " \
               "created_utc=%s, is_activated=%s, is_admin=%s, " \
               "is_mod=%s, is_banned=%s, ips=%s)>" \
               "" % (self.id, self.username, self.email, self.passhash,
                    self.created_utc, self.is_activated, self.is_admin,
                     self.is_mod, self.is_banned, self.ips)
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
        return "<Submission(id=%s, author_id=%s, title=%s, " \
               "url=%s, created_utc=%s, is_banned=%s)>" \
               "" % (self.id, self.author_id, self.title,
                     self.url, self.created_utc, self.is_banned)

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


