from flask import render_template
from sqlalchemy import *
from sqlalchemy.orm import relationship

from ruqqus.__main__ import Base


class CrossPosts(Base):

    __tablename__ = "cross_posts"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    board_id = Column(Integer, ForeignKey('boards.id'))

    board = relationship("Board", lazy="joined", innerjoin=True, primaryjoin="CrossPosts.board_id==Board.id")
    post = relationship("Board", lazy="joined", innerjoin=True, primaryjoin="CrossPosts.post_id==Submission.id")

    def __repr__(self):
        return f"<CrossPosts(id={self.id}, board_id={self.id}, post_id={self.post_id})>"
