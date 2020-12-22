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
    created_utc = Column(Integer, default=0)
    targetUser = Column(Integer, ForeignKey("users.id"), default=0)
    targetPost = Column(Integer, ForeignKey("submissions.id"), default=0)
    targetComment = Column(Integer, ForeignKey("comments.id"), default=0)
    targetLodge = Column(Integer, ForeignKey("lodges.id"), default=0)
    targetRule = Column(Boolean, ForeignKey("rules.id"), default=False)

    def __init__(self, *args, **kwargs):
        if "created_utc" not in kwargs:
            kwargs["created_utc"] = int(time.time())

    def __str__(self):
        # user actions
        if type >= 1 and type < 21:
            return f"{self.user_id.name} {self.type.description} {self.targetUser.name} at {self.created_date}"
        # lodge actions
        elif type >= 21 and type < 41:
            return f"{self.user_id.name} {self.type.description} {self.targetLodge.name} at {self.created_date}"

        # rule actions
        elif type >= 41 and type < 61:
            return f"{self.user_id.name} {self.type.description} {self.targetRule.id} at {self.created_date}"

        # comment actions
        elif type >= 61 and type < 81:
            return f"{self.user_id.name} {self.type.description} {self.targetComment.id} at {self.created_date}"

        # post actions
        elif type >= 61 and type < 81:
            return f"{self.user_id.name} {self.type.description} {self.targetPost.id} at {self.created_date}"





        elif