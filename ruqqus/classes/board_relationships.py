from ruqqus.helpers.base36 import *
from ruqqus.helpers.security import *
from sqlalchemy import *
from sqlalchemy.orm import relationship
from ruqqus.__main__ import Base, db, cache
import time

class ModRelationship(Base):
    __tablename__ = "mods"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    board_id = Column(Integer, ForeignKey("boards.id"))
    created_utc = Column(Integer, default=0)
    accepted = Column(Boolean, default=False)
    invite_rescinded=Column(Boolean, default=False)

    user=relationship("User", lazy="subquery")
    board=relationship("Board", lazy="subquery")

    def __init__(self, *args, **kwargs):
        if "created_utc" not in kwargs:
            kwargs["created_utc"] = int(time.time())

        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<Mod(id={self.id}, uid={self.uid}, board_id={self.board_id})>"


class BanRelationship(Base):

    __tablename__="bans"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    board_id = Column(Integer, ForeignKey("boards.id"))
    created_utc = Column(BigInteger, default=0)
    banning_mod_id=Column(Integer, ForeignKey("users.id"))
    is_active=Column(Boolean, default=False)

    user=relationship("User", uselist=False, primaryjoin="User.id==BanRelationship.user_id")
    banning_mod=relationship("User", uselist=False, primaryjoin="User.id==BanRelationship.banning_mod_id")
    board=relationship("Board", uselist=False)

    def __init__(self, *args, **kwargs):
        if "created_utc" not in kwargs:
            kwargs["created_utc"] = int(time.time())

        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<Ban(id={self.id}, uid={self.uid}, board_id={self.board_id})>"

class ContributorRelationship(Base):

    __tablename__="contributors"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    board_id = Column(Integer, ForeignKey("boards.id"))
    created_utc = Column(BigInteger, default=0)

    user=relationship("User", lazy="subquery")
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
        return f"<PostRel(id={self.id}, uid={self.uid}, board_id={self.board_id})>"
