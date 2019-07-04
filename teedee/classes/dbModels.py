from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import *
from os import environ
from __init__ import app

DBUNAME = "root"
DBPASS = ""
DB = "teedee"
DBPORT = 3306

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{0}:{1}@127.0.0.1/{2}?host=127.0.0.1?port={3}/charset=utf8/' \
                                        ''.format(DBUNAME, DBPASS, DB,DBPORT)

_engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
db = sessionmaker(bind=_engine)()
Base=declarative_base()

class User(Base):

    __tablename__="users"

    id = Column(BigInteger, primary_key=True)
    username = Column(String, default=None)
    email = Column(String, default=None)
    passhash = Column(String, default=None)
    created_utc = Column(BigInteger, default=0)
    is_activated = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    is_mod = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)

    def hashPass(self, password):
        self.hash = generate_password_hash(password, method='pbkdf2:sha512', salt_length=8)
        return self.hash

    def verifyPass(self, password):
        return check_password_hash(self.hash, password)

    def __repr__(self):
        return "<User(id=%s, username=%s, email=%s, passhash=%s, " \
               "created_utc=%s, is_activated=%s, is_admin=%s, " \
               "is_mod=%s, is_banned=%s)>" \
               "" % (self.id, self.username, self.email, self.passhash,
                    self.created_utc, self.is_activated, self.is_admin,
                     self.is_mod, self.is_banned)

class Submission(Base):

    __tablename__="submissions"

    id = Column(BigInteger, primary_key=True)
    author_id = Column(BigInteger, default=0)
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

    __tablename__="comments"

    id = Column(BigInteger, primary_key=True)
    author_id = Column(BigInteger, default=0)
    body = Column(String(10000), default=None)
    parent_submission = Column(BigInteger, default=0)
    parent_comment = Column(BigInteger, default=0)
    created_utc = Column(BigInteger, default=0)
    is_banned = Column(Boolean, default=False)

    def __repr__(self):
        return "<Comment(id=%s, author_id=%s, body=%s, parent_submission=%s, " \
               "parent_comment=%s, created_utc=%s, is_banned=%s)>" \
               "" % (self.id, self.author_id, self.body, self.parent_submission,
                   self.parent_comment, self.created_utc, self.is_banned)
