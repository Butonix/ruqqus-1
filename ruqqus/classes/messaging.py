from flask import *
from time import time, strftime, gmtime
from sqlalchemy import *
from sqlalchemy.orm import relationship

from ruqqus.helpers.base36 import *
from ruqqus.__main__ import Base


class Conversation(Base):

    __tablename__="conversations"
    id=Column(Integer, primarykey=True)
    author_id=Column(Integer, ForeignKey("User.id"))
    created_utc=Column(Integer)
    subject=Column(String(256))

    members=relationship("ConvoMember")


class Message(Base):

    __tablename__="messages"
    id=Column(Integer, primarykey=True)
    author_id=Column(Integer, ForeignKey("User.id"))
    created_utc=Column(Integer)
    body=Column(String(10000))
    body_html=Column(String(15000))
    has_read=Column(Boolean)

    conversation=relationship("Conversation")


class ConvoMember(Base):

    __tablename__="conve_member"
    id=Column(Integer, primarykey=True)
    user_id=Column(Integer, ForeignKey("User.id"))
    convo_id=Column(Integer, ForeignKey("Conversation.id"))

    user=relationship("User")
    conversation=relationship("Conversation")