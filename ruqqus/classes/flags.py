from sqlalchemy import *
from ruqqus.__main__ import Base, db, cache


class Flag(Base):

    __tablename__="flags"

    id=Column(Integer, primary_key=True)
    post_id=Column(Integer, ForeignKey("submissions.id"))
    user_id=Column(Integer, ForeignKey("users.id"))
    created_utc=Column(Integer)

    def __repr__(self):

        return f"<Flag(id={self.id})>"

class CommentFlag(Base):

    __tablename__="commentflags"

    id=Column(Integer, primary_key=True)
    user_id=Column(Integer, ForeignKey("users.id"))
    comment_id=Column(Integer, ForeignKey("comments.id"))
    created_utc=Column(Integer)

    def __repr__(self):

        return f"<CommentFlag(id={self.id})>"
