from sqlalchemy import *
from sqlalchemy.orm import relationship, deferred
import time
from ruqqus.helpers.base36 import *
from ruqqus.helpers.security import *
from ruqqus.helpers.lazy import *
from ruqqus.helpers.session import *
import ruqqus.helpers.aws as aws
from .mix_ins import *
from ruqqus.__main__ import Base, db, cache


class DMs(Base, Stndrd, Age_times):
    __tablename__ = "dms"

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    subject = Column(String(256))
    created_utc = Column(Integer)
    edited_utc = Column(BigInteger, default=0)
    body=Column(String(2500), default="")
    body_html=Column(String(5000), default="")
    embed_url=Column(String(256), default="")
    domain_ref=Column(Integer, ForeignKey("domains.id"))
    is_approved=Column(Integer, ForeignKey("users.id"), default=0)
    approved_utc=Column(Integer, default=0)
    parent_dm_id = Column(Integer, ForeignKey("dms.id"))
    is_banned=Column(Boolean, default=False)
    flags = relationship("Flag", lazy="dynamic", backref="submission")


    def __init__(self, **kwargs):
        kwargs["created_utc"] = int(time.time())

        super().__init__(**kwargs)

    def __repr__(self):
        return f"<DM(sender={self.name}, subject={self.subject})>"