from base import *
from sqlalchemy import *
from werkzeug.security import generate_password_hash, check_password_hash



class User(Base):

    __tablename__="users"

    id = Column(BigInteger, primary_key=True)
    username = Column(String)
    email = Column(String)
    passhash = Column(String)
    created_utc = Column(BigInteger)
    is_activated = Column(Boolean)
    is_admin = Column(Boolean)
    is_mod = Column(Boolean)
    is_banned = Column(Boolean)

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
    author_id = Column(BigInteger)
    title = Column(String)
    url = Column(String)
    created_utc = Column(BigInteger)
    is_banned = Column(Boolean)

    def __repr__(self):
        return "<Submission(id=%s, author_id=%s, title=%s, " \
               "url=%s, created_utc=%s, is_banned=%s)>" \
               "" % (self.id, self.author_id, self.title,
                     self.url, self.created_utc, self.is_banned)


class Comment(Base):

    __tablename__="submissions"

    id = Column(BigInteger, primary_key=True)
    author_id = Column(BigInteger)
    body = Column(String)
    parent_submission = Column(BigInteger)
    parent_comment = Column(BigInteger)
    created_utc = Column(BigInteger)
    is_banned = Column(Boolean)

    def __repr__(self):
        return "<Comment(id=%s, author_id=%s, body=%s, parent_submission=%s, " \
               "parent_comment=%s, created_utc=%s, is_banned=%s)>" \
               "" % (self.id, self.author_id, self.body, self.parent_submission,
                   self.parent_comment, self.created_utc, self.is_banned)


