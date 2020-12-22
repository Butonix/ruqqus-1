from ruqqus.helpers.base36 import *
from ruqqus.helpers.security import *
from sqlalchemy import *
from sqlalchemy.orm import relationship
from ruqqus.__main__ import Base, cache
from .mix_ins import *
import time


class ModAction(Base, Stndrd, Age_times):
    __tablename__ = "modactions"
    id = Column(BigInteger, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    board_id = Column(Integer, ForeignKey("boards.id"))
    kind = Column(String(32), ForeignKey("kinds.id"))
    target_user_id = Column(Integer, ForeignKey("users.id"), default=0)
    target_submission_id = Column(Integer, ForeignKey("submissions.id"), default=0)
    target_comment_id = Column(Integer, ForeignKey("comments.id"), default=0)
    #targetLodge = Column(Integer, ForeignKey("lodges.id"), default=0)
    #targetRule = Column(Boolean, ForeignKey("rules.id"), default=False)

    created_utc = Column(Integer, default=0)


    user = relationship("User", lazy="joined", primaryjoin="User.id==ModAction.user_id")
    target_user = relationship("User", lazy="joined", primaryjoin="User.id==ModAction.target_user_id")
    target_board = relationship("Board", lazy="joined")
    #target_lodge = relationship("Lodge", lazy="joined")
    #target_rule = relationship("Rule", lazy="joined")
    target_post = relationship("Submission", lazy="joined")
    target_comment = relationship("Comment", lazy="joined")


    def __init__(self, *args, **kwargs):
        if "created_utc" not in kwargs:
            kwargs["created_utc"] = int(time.time())

    def __repr__(self):
        return f"<ModAction(id={self.base36id})>"

    @property
    def str_mod(self):
        return ACTIONTYPES[self.kind]["str_mod"].format()

    @property
    def str_user(self):
        return ACTIONTYPES[self.kind]["str_user"].format()





ACTIONTYPES={
    "kick_post":{
        "str_mod":"[@{self.user.username}]({self.user.permalink}) kicked post [{self.target_post.title}]({self.target_post.url})",
        "str_user":"A Guildmaster kicked post [{self.target_post.title}]({self.target_post.url})"
    },
    "yank_post":{
        "str_mod":"[@{self.user.username}]({self.user.permalink}) yanked post [{self.target_post.title}]({self.target_post.url})",
        "str_user":"A Guildmaster yanked post [{self.target_post.title}]({self.target_post.url})"
    },
    "exile_user":{
        "str_mod":"[@{self.user.username}]({self.user.permalink}) exiled user [@{self.target_user.username}]({self.target_user.permalink})",
        "str_user":"A Guildmaster exiled user [@{self.target_user.username}]({self.target_user.permalink})"
    },
    "unexile_user":{},
    "contrib_user":{},
    "uncontrib_user":{},
    "herald_comment":{},
    "herald_post":{},
    "unherald_comment":{},
    "unherald_post":{},
    "pin_comment":{},
    "unpin_comment":{},
    "pin_post":{},
    "unpin_post":{}
}