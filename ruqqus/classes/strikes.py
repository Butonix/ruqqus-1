from .mix_ins import *
from flask import *
import time
from sqlalchemy import *
from sqlalchemy.orm import relationship, deferred
from ruqqus.helpers.base36 import *
from ruqqus.helpers.lazy import lazy
from ruqqus.__main__ import Base, cache


class Strike(Base, Stndrd, Age_times):

    __tablename__ = "strikes"
    id = Column(BigInteger, ForeignKey("punishments.i") primary_key=True)
    name = Column(String(256))
    description = Column(String)
    created_utc = Column(BigInteger, default=0)

    punishments = relationship("Punishment", primaryjoin="Strike.id==Punishment.strike_id")

    def __init__(self, *args, **kwargs):
        if "created_utc" not in kwargs:
            kwargs["created_utc"] = int(time.time())
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<Strike(id={self.id}, board_id={self.board_id})>"


class Punishment(Base, Stndrd, Age_times):

    __tablename__ = "earnedstrikes"
    id = Column(BigInteger, primary_key=True)
    strike_id = Column(Integer, ForeignKey("users.id"))
    kind = Column(String(100))
    punishment = Column(String(100))
    created_utc = Column(BigInteger, default=0)

    def __init__(self, *args, **kwargs):
        if "created_utc" not in kwargs:
            kwargs["created_utc"] = int(time.time())
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<Punishment(id={self.id}, strike_id={self.strike_id})>"


class EarnedStrike(Base, Stndrd, Age_times):

    __tablename__ = "earnedstrikes"
    id = Column(BigInteger, primary_key=True)
    strike_id = Column(Integer, ForeignKey("strikes.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("submissions.id"))
    comment_id = Column(Integer, ForeignKey("submissions.id"))
    board_id = Column(Integer, ForeignKey("boards.id"))
    target_user_id = Column(Integer, ForeignKey("users.id"))
    created_utc = Column(BigInteger, default=0)

    strike = relationship("Strike", primaryjoin="EarnedStrike.strike_id==Strike.id")
    def __init__(self, *args, **kwargs):
        if "created_utc" not in kwargs:
            kwargs["created_utc"] = int(time.time())
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<EarnedStrike(id={self.id}, board_id={self.board_id})>"

    def evalPunishment(self):
        return self.strike.punishments.punishment