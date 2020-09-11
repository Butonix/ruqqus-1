from flask import *
from time import time, strftime, gmtime
from sqlalchemy import *
from sqlalchemy.orm import relationship

from .mix_ins import Stndrd, Age_times
from ruqqus.helpers.base36 import *
from ruqqus.__main__ import Base


class Conversation(Base, Stndrd, Age_times):

    __tablename__="conversations"
    id=Column(Integer, primary_key=True)
    author_id=Column(Integer, ForeignKey("users.id"))
    created_utc=Column(Integer)
    subject=Column(String(256))

    members=relationship("ConvoMember")
    _messages=relationship("Message", lazy="dynamic")

    
    def __repr__(self):

        return f"<Conversation(id={self.id})>"

    @property
    def permalink(self):
        return f"/message/{self.base36id}"

    @property
    def messages(self):

        return self._messages.order_by(Message.created_utc.asc()).all()


class Message(Base, Stndrd, Age_times):

    __tablename__="messages"
    id=Column(Integer, primary_key=True)
    author_id=Column(Integer, ForeignKey("users.id"))
    created_utc=Column(Integer)
    body=Column(String(10000))
    body_html=Column(String(15000))
    distinguish_level=Column(Integer, default=0)

    conversation=relationship("Conversation")

    
    def __repr__(self):

        return f"<Message(id={self.id})>"

    @property
    def permalink(self):
        return f"{self.conversation.permalink}/{self.base36id}"

class ConvoMember(Base, Stndrd, Age_times):

    __tablename__="convo_member"
    id=Column(Integer, primary_key=True)
    user_id=Column(Integer, ForeignKey("users.id"))
    convo_id=Column(Integer, ForeignKey("conversations.id"))

    user=relationship("User")
    conversation=relationship("Conversation")


    def __repr__(self):

        return f"<ConvoMember(id={self.id})>"

class MessageNotif(Base, Stndrd, Age_times):

    __tablename__="message_notifications"
    id=Column(Integer, primary_key=True)
    user_id=Column(Integer, ForeignKey("users.id"))
    message_id=Column(Integer, ForeignKey("messages.id"))
    has_read=Column(Boolean, default=False)