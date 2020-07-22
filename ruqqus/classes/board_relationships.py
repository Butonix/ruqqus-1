from ruqqus.helpers.base36 import *
from ruqqus.helpers.security import *
from sqlalchemy import *
from sqlalchemy.orm import relationship
from ruqqus.__main__ import Base, cache
from .mix_ins import *
import time

class ModRelationship(Base):
    __tablename__ = "mods"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    board_id = Column(Integer, ForeignKey("boards.id"))
    created_utc = Column(Integer, default=0)
    accepted = Column(Boolean, default=False)
    invite_rescinded=Column(Boolean, default=False)

    user=relationship("User", lazy="joined")
    board=relationship("Board", lazy="joined")

    def __init__(self, *args, **kwargs):
        if "created_utc" not in kwargs:
            kwargs["created_utc"] = int(time.time())

        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<Mod(id={self.id}, uid={self.user_id}, board_id={self.board_id})>"


class BanRelationship(Base, Stndrd, Age_times):

    __tablename__="bans"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    board_id = Column(Integer, ForeignKey("boards.id"))
    created_utc = Column(BigInteger, default=0)
    banning_mod_id=Column(Integer, ForeignKey("users.id"))
    is_active=Column(Boolean, default=False)
    mod_note=Column(String(128), default="")

    user=relationship("User", lazy="joined", primaryjoin="User.id==BanRelationship.user_id")
    banning_mod=relationship("User", lazy="joined", primaryjoin="User.id==BanRelationship.banning_mod_id")
    board=relationship("Board")

    def __init__(self, *args, **kwargs):
        if "created_utc" not in kwargs:
            kwargs["created_utc"] = int(time.time())

        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<Ban(id={self.id}, uid={self.uid}, board_id={self.board_id})>"

class ContributorRelationship(Base, Stndrd, Age_times):

    __tablename__="contributors"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    board_id = Column(Integer, ForeignKey("boards.id"))
    created_utc = Column(BigInteger, default=0)
    is_active=Column(Boolean, default=True)
    approving_mod_id=Column(Integer, ForeignKey("users.id"))

    user=relationship("User", lazy="joined", primaryjoin="User.id==ContributorRelationship.user_id")
    approving_mod=relationship("User", lazy='joined', primaryjoin="User.id==ContributorRelationship.approving_mod_id")
    board=relationship("Board", lazy="subquery")

    def __init__(self, *args, **kwargs):
        if "created_utc" not in kwargs:
            kwargs["created_utc"] = int(time.time())

        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<Contributor(id={self.id}, uid={self.uid}, board_id={self.board_id})>"


class PostRelationship(Base):

    __tablename__="postrels"
    id=Column(BigInteger, primary_key=True)
    post_id=Column(Integer, ForeignKey("submissions.id"))
    board_id=Column(Integer, ForeignKey("boards.id"))

    post=relationship("Submission", lazy="subquery")
    board=relationship("Board", lazy="subquery")

    def __repr__(self):
        return f"<PostRel(id={self.id}, pid={self.post_id}, board_id={self.board_id})>"


class BoardBlock(Base, Stndrd, Age_times):

    __tablename__="boardblocks"

    id=Column(BigInteger, primary_key=True)
    user_id=Column(Integer, ForeignKey("users.id"))
    board_id=Column(Integer, ForeignKey("boards.id"))
    created_utc=Column(Integer)

    user=relationship("User")
    board=relationship("Board")

    def __repr__(self):
        return f"<BoardBlock(id={self.id}, uid={self.user_id}, board_id={self.board_id})>"