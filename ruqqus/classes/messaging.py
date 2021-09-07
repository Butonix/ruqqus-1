from flask import *
import re
from time import time, strftime, gmtime
from sqlalchemy import *
from sqlalchemy.orm import relationship

from .mix_ins import Stndrd, Age_times
from ruqqus.helpers.base36 import *
from ruqqus.helpers.lazy import lazy
from ruqqus.__main__ import Base


class Conversation(Base, Stndrd, Age_times):

    __tablename__="conversations"
    id=Column(Integer, primary_key=True)
    author_id=Column(Integer, ForeignKey("users.id"))
    created_utc=Column(Integer)
    subject=Column(String(256))
    board_id=Column(Integer, ForeignKey("boards.id"))

    _members=relationship("ConvoMember", lazy="joined")
    _messages=relationship("Message", lazy="joined")

    board = relationship("Board", lazy="joined")
    author=relationship("User", lazy="joined")

    
    def __repr__(self):

        return f"<Conversation(id={self.base36id})>"

    @property
    def json_core(self):

        data={
            "id":self.base36id,
            "subject":self.subject,
            "created_utc":self.created_utc,
            "author_name": self.author.username if not self.author.is_deleted else None
        }

        if self.board:
            data["guild"]=self.board.name

    @property
    def json(self):
        data=self.json_core

        data['messages'] = [x.json_core for x in self.messages]

        return data
    


    @property
    def permalink(self):

        output = self.subject.lower()

        output = re.sub('&\w{2,3};', '', output)

        output = [re.sub('\W', '', word) for word in output.split()]
        output = [x for x in output if x][0:6]

        output = '-'.join(output)

        if not output:
            output = '-'

        return f"/messages/{self.base36id}/{output}"

    def has_member(self, user):
        if user.id in [x.user_id for x in self.members]:
            return True

        if self.board and self.board.has_mod(user, perm="mail"):
            return True

        return False

    @property
    def members(self):

        if self.board:
            users = [x.user for x in self.board.mods_list if x.perm_mail]

        else:
            users=[]

        return list(set(users+self._members))

    @property
    @lazy
    def messages(self):
        return sorted(self._messages, key=lambda x: x.id)
    

    @property
    def fullname(self):
        return f"t6_{self.base36id}"




class Message(Base, Stndrd, Age_times):

    __tablename__="messages"
    id=Column(Integer, primary_key=True)
    author_id=Column(Integer, ForeignKey("users.id"))
    created_utc=Column(Integer)
    body=Column(String(10000))
    body_html=Column(String(15000))
    distinguish_level=Column(Integer, default=0)
    convo_id=Column(Integer, ForeignKey("conversations.id"))
    creation_ip = Column(String(64))
    creation_region = Column(String(2))

    conversation=relationship("Conversation")
    author=relationship("User", lazy="joined")

    def __repr__(self):

        return f"<Message(id={self.base36id}, from={self.author.username})>"

    @property
    def permalink(self):
        return f"{self.conversation.permalink}/{self.base36id}"

    @property
    def convo_fullname(self):
        return f"t6_{base36encode(self.convo_id)}"


    @property
    def json_core(self):
        data= {
            "id": self.base36id,
            "created_utc": self.created_utc,
            "body": self.body,
            "body_html": self.body_html,
            "author_name": self.author.username if not self.author.is_deleted else None,
            "conversation_id": self.conversation.base36id
        }

        if self.distinguish_level:
            data["distinguished"]=True

    @property
    def json(self):
        data=self.json_core

        data["author"]=self.author.json_core

        return data
    
    
    

class ConvoMember(Base, Stndrd, Age_times):

    __tablename__="convo_member"
    id=Column(Integer, primary_key=True)
    user_id=Column(Integer, ForeignKey("users.id"))
    convo_id=Column(Integer, ForeignKey("conversations.id"))

    user=relationship("User")
    conversation=relationship("Conversation")


    def __repr__(self):

        return f"<ConvoMember(id={self.base36id})>"

class MessageNotif(Base, Stndrd, Age_times):

    __tablename__="message_notifications"
    id=Column(Integer, primary_key=True)
    user_id=Column(Integer, ForeignKey("users.id"))
    message_id=Column(Integer, ForeignKey("messages.id"))
    has_read=Column(Boolean, default=False)