from ruqqus.helpers.base36 import *
from ruqqus.helpers.security import *
from sqlalchemy import *
from sqlalchemy.orm import relationship
from ruqqus.__main__ import Base, cache
from .mix_ins import *
import time


class ModAction(Base, Stndrd, Age_times):
    __tablename__ = "modactions"
    id = Column(BigInteger, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    board_id = Column(Integer, ForeignKey("boards.id"))
    kind = Column(Integer, ForeignKey("kinds.id"))
    target_user_id = Column(Integer, ForeignKey("users.id"), default=0)
    target_submission_id = Column(Integer, ForeignKey("submissions.id"), default=0)
    target_comment_id = Column(Integer, ForeignKey("comments.id"), default=0)
    #targetLodge = Column(Integer, ForeignKey("lodges.id"), default=0)
    #targetRule = Column(Boolean, ForeignKey("rules.id"), default=False)

    created_utc = Column(Integer, default=0)


    user = relationship("User", lazy="joined", primaryjoin="User.id==ModAction.user_id")
    target_user = relationship("User", lazy="joined", primaryjoin="User.id==ModAction.target_user_id")
    target_board = relationship("Board", lazy="joined")
    #target_lodge = relationship("Lodge", lazy="joined")
    #target_rule = relationship("Rule", lazy="joined")
    target_post = relationship("Submission", lazy="joined")
    target_comment = relationship("Comment", lazy="joined")
    kind_rel = relationship("kind", lazy="joined")


    def __init__(self, *args, **kwargs):
        if "created_utc" not in kwargs:
            kwargs["created_utc"] = int(time.time())

    def __repr__(self):
        return f"<ModAction(id={self.base36id})>"


    def __str__(self):
        # user actions
        if kind >= 1 and kind <= 100:
            return f"{self.user.username} {self.kind_rel.description} {self.target_user.username} at {self.created_date}"
        # lodge actions
        elif kind >= 101 and kind <= 200:
            return f"{self.user.username} {self.kind_rel.description} {self.target_lodge.name} at {self.created_date}"

        # rule actions
        elif kind >= 201 and kind <= 300:
            return f"{self.user.usernamee} {self.kind_rel.description} {self.targetRule.id} at {self.created_date}"

        # comment actions
        elif kind >= 301 and kind <= 400:
            return f"{self.user.username} {self.kind_rel.description} {self.target_comment.id} at {self.created_date}"

        # post actions
        elif kind >= 401 and kind <= 500:
            return f"{self.user.username} {self.kind_rel.description} {self.target_post.id} at {self.created_date}"




class kind(Base, Stndrd, Age_times):
    __tablename__ = "kinds"
    id = Column(BigInteger, primary_key=True)
    description = Column(String(250), default="")
    user_id = Column(Integer, ForeignKey("users.id"))
    board_id = Column(Integer, ForeignKey("boards.id"))
    created_utc = Column(Integer, default=0)

    def __init__(self, *args, **kwargs):
        if "created_utc" not in kwargs:
            kwargs["created_utc"] = int(time.time())

