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
    def str(self):
        return ACTIONTYPES[self.kind]["str"].format()


ACTIONTYPES={
    "kick_post":{
        "str":"kicked post [{self.target_post.title}]({self.target_post.url})",
        "icon":"fa-sign-out fa-flip-horizontal text-warning"
    },
    "yank_post":{
        "str":"yanked post [{self.target_post.title}]({self.target_post.url})",
        "icon":"fa-hand-lizard text-muted"
    },
    "exile_user":{
        "str":"exiled user [@{self.target_user.username}]({self.target_user.permalink})",
        "icon":"fa-user-slash text-warning"
    },
    "unexile_user":{
        "str":"un-exiled user [@{self.target_user.username}]({self.target_user.permalink})",
        "icon": "fa-user-slash text-muted"
    },
    "contrib_user":{
        "str":"added [@{self.target_user.username}]({self.target_user.permalink}) as an approved contributor",
        "icon": "fa-user-plus text-info"
    },
    "uncontrib_user":{
        "str":"[@{self.user.username}]({self.user.permalink}) added [@{self.target_user.username}]({self.target_user.permalink}) as an approved contributor",
        "icon": "fa-user-plus text-muted"
    },
    "herald_comment":{
        "str":"heralded their [comment]({self.target_comment.permalink})",
        "icon": "fa-crown text-warning",
        "show_mod":True
    },
    "herald_post":{
        "str_mod":"heralded their post [{self.target_post.title}]({self.target_post.permalink})",
        "icon": "fa-crown text-warning",
        "show_mod":True
    },
    "unherald_comment":{
        "str":"un-heralded their [comment]({self.target_comment.permalink})",
        "icon": "fa-crown text-muted",
        "show_mod":True
        },
    "unherald_post":{
        "str":"un-heralded their post [{self.target_post.title}]({self.target_post.permalink})",
        "icon": "fa-crown text-muted",
        "show_mod":True
    },
    "pin_comment":{
        "str":"pinned a [comment]({self.target_comment.permalink})",
        "icon":"fa-thumbtack fa-rotate--45 text-info",
    },
    "unpin_comment":{
        "str":"un-pinned a [comment]({self.target_comment.permalink})",
        "icon":"fa-thumbtack fa-rotate--45 text-muted",
    },
    "pin_post":{
        "str":"pinned a [post]({self.target_post.permalink})",
        "icon":"fa-thumbtack fa-rotate--45 text-info",
    },
    "unpin_post":{
        "str":"un-pinned a [post]({self.target_post.permalink})",
        "icon":"fa-thumbtack fa-rotate--45 text-muted",
    },
    "invite_mod":{
        "str":"invited [@{self.target_user.username}]({self.target_user.permalink}) as a Guildmaster"
        "icon":"fa-crown text-info"
    },
    "uninvite_mod":{
        "str":"rescinded Guildmaster invitation to [@{self.target_user.username}]({self.target_user.permalink})"
        "icon":"fa-crown text-muted"
    },
    "remove_mod":{
        "str":"removed Guildmaster [@{self.target_user.username}]({self.target_user.permalink})"
        "icon":"fa-crown text-warning"
    },
    "add_mod":{
        "str":"added [@{self.target_user.username}]({self.target_user.permalink}) as a Guildmaster"
        "icon":"fa-crown text-success",
        "show_mod":True
    }
}