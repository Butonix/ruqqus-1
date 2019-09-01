from flask import render_template
from sqlalchemy import *
from sqlalchemy.orm import relationship

from ruqqus.__main__ import Base, db

class BadgeDef(Base):

    __tablename__="badge_defs"

    id = Column(BigInteger, primary_key=True)
    name=Column(String(64))
    description=Column(String(64))
    icon=Column(String(64))

    def __repr__(self):

        return f"<BadgeDef(badge_id={self.id})>"

    @property
    def path(self):

        return f"/assets/images/badges/{self.icon}"
    

class Badge(Base):

    __tablename__="badges"

    id=Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey('users.id'))
    badge_id=Column(Integer, ForeignKey("badge_defs.id"))
    description=Column(String(64))
    url=Column(String(256))
    created_utc=Column(Integer)
    badge=relationship("BadgeDef", uselist=False)

    def __repr__(self):

        return f"<Badge(user_id={self.user_id}, badge_id={self.badge_id})>"

    @property
    def text(self):
        if self.description:
            return self.description
        else:
            return self.badge.description

    @property
    def type(self):
        return self.badge.id

    @property
    def name(self):
        return self.badge.name


    @property
    def path(self):
        return self.badge.path

    @property
    def rendered(self):

        return render_template("badge.html", b=self)
