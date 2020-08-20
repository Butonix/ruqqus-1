from sqlalchemy import *
from ruqqus.__main__ import Base, cache

reasons={
	1: "URL shorteners are not allowed.",
	3: "Piracy is not allowed.",
    4: "Sites hosting digitally malicious content are not allowed.",
    5: "Spam",
    6: "Doxxing is not allowed."
}

class Domain(Base):

    __tablename__="domains"
    id=Column(Integer, primary_key=True)
    domain=Column(String)
    can_submit=Column(Boolean, default=False)
    can_comment=Column(Boolean, default=False)
    reason=Column(String)
    show_thumbnail=Column(Boolean, default=False)
    embed_function=Column(String(64), default=None)
    
    @property
    def reason_text(self):
    	return reasons.get(self.reason)

class BadLink(Base):

    __tablename__="badlinks"
    id=Column(Integer, primary_key=True)
    reason=Column(Integer)
    link=Column(String(512))
    autoban=Column(Boolean, default=False)

    @property
    def reason_text(self):
        return reasons.get(self.reason)
    