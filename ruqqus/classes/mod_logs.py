from ruqqus.helpers.base36 import *
from ruqqus.helpers.security import *
from sqlalchemy import *
from sqlalchemy.orm import relationship
from ruqqus.__main__ import Base, cache
from .mix_ins import *
import time


class ModLog(Base, Stndrd, Age_times):
    __tablename__ = "modLogs"
    id = Column(BigInteger, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    board_id = Column(Integer, ForeignKey("boards.id"))
    type = Column(Integer, ForeignKey("types.id"))
    targetUser = Column(Integer, ForeignKey("users.id"), default=0)
    targetPost = Column(Integer, ForeignKey("submissions.id"), default=0)
    targetComment = Column(Integer, ForeignKey("comments.id"), default=0)
    targetLodge = Column(Integer, ForeignKey("lodges.id"), default=0)
    targetRule = Column(Boolean, ForeignKey("rules.id"), default=False)

    created_utc = Column(Integer, default=0)


    user = relationship("User", lazy="joined")
    target_user = relationship("User", lazy="joined")
    target_board = relationship("Board", lazy="joined")
    target_lodge = relationship("Lodge", lazy="joined")
    target_rule = relationship("Rule", lazy="joined")
    target_post = relationship("Submission", lazy="joined")
    target_comment = relationship("Comment", lazy="joined")
    type_rel = relationship("Type", lazy="joined")


    def __init__(self, *args, **kwargs):
        if "created_utc" not in kwargs:
            kwargs["created_utc"] = int(time.time())


    def __str__(self):
        # user actions
        if type >= 1 and type <= 100:
            return f"{self.user.username} {self.type_rel.description} {self.target_user.username} at {self.created_date}"
        # lodge actions
        elif type >= 101 and type <= 200:
            return f"{self.user.username} {self.type_rel.description} {self.target_lodge.name} at {self.created_date}"

        # rule actions
        elif type >= 201 and type <= 300:
            return f"{self.user.usernamee} {self.type_rel.description} {self.targetRule.id} at {self.created_date}"

        # comment actions
        elif type >= 301 and type <= 400:
            return f"{self.user.username} {self.type_rel.description} {self.target_comment.id} at {self.created_date}"

        # post actions
        elif type >= 401 and type <= 500:
            return f"{self.user.username} {self.type_rel.description} {self.target_post.id} at {self.created_date}"
