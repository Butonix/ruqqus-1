from flask import *
from time import time, strftime, gmtime
from sqlalchemy import *
from sqlalchemy.orm import relationship

from .mixins import Stndrd, Age_times
from ruqqus.helpers.base36 import *
from ruqqus.__main__ import Base


class Conversation(Base, Stndrd, Age_times):

    __tablename__="conversations"
    id=Column(Integer, primarykey=True)
    author_id=Column(Integer, ForeignKey("User.id"))
    created_utc=Column(Integer)
    subject=Column(String(256))

    members=relationship("ConvoMember")
    messages=relationship("Message", lazy="joinedload")

    
    def __repr__(self):

        return f"<Conversation(id={self.id})>"

    @property
    def permalink(self):
        return f"/message/{self.base36id}"


class Message(Base, Stndrd, Age_times):

    __tablename__="messages"
    id=Column(Integer, primarykey=True)
    author_id=Column(Integer, ForeignKey("User.id"))
    created_utc=Column(Integer)
    body=Column(String(10000))
    body_html=Column(String(15000))
    has_read=Column(Boolean, default=False)

    conversation=relationship("Conversation")

    
    def __repr__(self):

        return f"<Message(id={self.id})>"

    @property
    def permalink(self):
        return f"{self.conversation.permalink}/{self.base36id}"

class ConvoMember(Base, Stndrd, Age_times):

    __tablename__="conve_member"
    id=Column(Integer, primarykey=True)
    user_id=Column(Integer, ForeignKey("User.id"))
    convo_id=Column(Integer, ForeignKey("Conversation.id"))

    user=relationship("User")
    conversation=relationship("Conversation")


    def __repr__(self):

        return f"<ConvoMember(id={self.id})>"