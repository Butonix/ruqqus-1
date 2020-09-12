from flask import render_template
from sqlalchemy import *
from sqlalchemy.orm import relationship

from ruqqus.__main__ import Base


class crossPosts(Base):

    __tablename__ = "cross_posts"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    board_id = Column(Integer, ForeignKey('boards.id'))

    def __repr__(self):
        return f"<crossPosts(id={self.id}, board_id={self.id}, post_id={self.post_id})>"
