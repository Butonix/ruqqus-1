from ruqqus.helpers.base36 import *
from ruqqus.helpers.security import *
from sqlalchemy import *
from sqlalchemy.orm import relationship
from ruqqus.__main__ import Base, cache
from .mix_ins import *
import time

class Favorite(Base, Stndrd):
    __tablename__ = "favorites"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("submissions.id"), default=0)
    comment_id = Column(Integer, ForeignKey("comments.id"), default=0)
    created_utc = Column(Integer, default=0)

    post = relationship("Submission", lazy="joined")
    comment = relationship("Comment", lazy="joined")

    def __init__(self, *args, **kwargs):
        if "created_utc" not in kwargs:
            kwargs["created_utc"] = int(time.time())

        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<Favorite(id={self.id}, uid={self.user_id}, board_id={self.board_id})>"