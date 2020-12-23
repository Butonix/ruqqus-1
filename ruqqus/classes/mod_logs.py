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
    kind = Column(String(32))
    target_user_id = Column(Integer, ForeignKey("users.id"), default=0)
    target_submission_id = Column(Integer, ForeignKey("submissions.id"), default=0)
    target_comment_id = Column(Integer, ForeignKey("comments.id"), default=0)
    #targetLodge = Column(Integer, ForeignKey("lodges.id"), default=0)
    #targetRule = Column(Boolean, ForeignKey("rules.id"), default=False)
    note=Column(String(64), default=None)
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

        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<ModAction(id={self.base36id})>"

    @property
    def actiontype(self):
        return ACTIONTYPES[self.kind]

    @property
    def str_user(self):
        output =  self.actiontype["str"].format(self=self)
        if self.user_id==1 or self.actiontype.get("show_mod"):
            output = f'<a href="{self.user.permalink}" target="_blank">@{self.user.username}</a> {output}.'
        else:
            output = f"A Guildmaster {output}."

        return output

    @property
    def str_mod(self):
        output =  self.actiontype["str"].format(self=self)
        output = f'<a href="{self.user.permalink}" target="_blank">@{self.user.username}</a> {output}.'

        return output

    @property
    def icon(self):
        return self.actiontype['icon']
    
    


ACTIONTYPES={
    "kick_post":{
        "str":'kicked post <a href="{self.target_post.url}" target="_blank">{self.target_post.title}</a>',
        "icon":"fa-sign-out fa-flip-horizontal text-warning"
    },
    "approve_post":{
        "str":'approved post <a href="{self.target_post.url}" target="_blank">{self.target_post.title}</a>',
        "icon":"fa-check text-success"
    },    
    "yank_post":{
        "str":'yanked post <a href="{self.target_post.url}" target="_blank">{self.target_post.title}</a>',
        "icon":"fa-hand-lizard text-muted"
    },
    "exile_user":{
        "str":'exiled user <a href="{self.target_user.permalink}" target="_blank">@{self.target_user.username}</a>',
        "icon":"fa-user-slash text-warning"
    },
    "unexile_user":{
        "str":'un-exiled user <a href="{self.target_user.permalink}" target="_blank">@{self.target_user.username}</a>',
        "icon": "fa-user-slash text-muted"
    },
    "contrib_user":{
        "str":'added contributor <a href="{self.target_user.permalink}" target="_blank">@{self.target_user.username}</a>',
        "icon": "fa-user-plus text-info"
    },
    "uncontrib_user":{
        "str":'removed contributor <a href="{self.target_user.permalink}" target="_blank">@{self.target_user.username}</a>',
        "icon": "fa-user-plus text-muted"
    },
    "herald_comment":{
        "str":'heralded their <a href="{self.target_comment.permalink}" target="_blank">comment</a>',
        "icon": "fa-crown text-warning",
        "show_mod":True
    },
    "herald_post":{
        "str_mod":'heralded their post <a href="{self.target_post.url}" target="_blank">{self.target_post.title}</a>',
        "icon": "fa-crown text-warning",
        "show_mod":True
    },
    "unherald_comment":{
        "str":'un-heralded their <a href="{self.target_comment.permalink}" target="_blank">comment</a>',
        "icon": "fa-crown text-muted",
        "show_mod":True
        },
    "unherald_post":{
        "str":'un-heralded their post <a href="{self.target_post.url}" target="_blank">{self.target_post.title}</a>',
        "icon": "fa-crown text-muted",
        "show_mod":True
    },
    "pin_comment":{
        "str":'pinned a <a href="{self.target_comment.permalink}" target="_blank">comment</a>',
        "icon":"fa-thumbtack fa-rotate--45 text-info",
    },
    "unpin_comment":{
        "str":'un-pinned a <a href="{self.target_comment.permalink}" target="_blank">comment</a>',
        "icon":"fa-thumbtack fa-rotate--45 text-muted",
    },
    "pin_post":{
        "str":'pinned post <a href="{self.target_post.url}" target="_blank">{self.target_post.title}</a>',
        "icon":"fa-thumbtack fa-rotate--45 text-info",
    },
    "unpin_post":{
        "str":'un-pinned post <a href="{self.target_post.url}" target="_blank">{self.target_post.title}</a>',
        "icon":"fa-thumbtack fa-rotate--45 text-muted",
    },
    "invite_mod":{
        "str":'invited Guildmaster <a href="{self.target_user.permalink}" target="_blank">@{self.target_user.username}</a>',
        "icon":"fa-crown text-info"
    },
    "uninvite_mod":{
        "str":'rescinded Guildmaster invitation to <a href="{self.target_user.permalink}" target="_blank">@{self.target_user.username}</a>',
        "icon":"fa-crown text-muted"
    },
    "accept_mod_invite":{
        "str":'accepted Guildmaster invitation',
        "icon":"fa-crown text-warning",
        "show_mod":True
    },
    "remove_mod":{
        "str":'removed Guildmaster <a href="{self.target_user.permalink}" target="_blank">@{self.target_user.username}</a>',
        "icon":"fa-crown text-danger"
    },
    "add_mod":{
        "str":'added Guildmaster <a href="{self.target_user.permalink}" target="_blank">@{self.target_user.username}</a>',
        "icon":"fa-crown text-success",
        "show_mod":True
    },
    "update_settings":{
        "str":'updated setting ({self.note})',
        "icon":"fa-cog text-info",
        "show_mod":True
    },
    "update_appearance":{
        "str":'updated appearance ({self.note})',
        "icon":"fa-palette text-info",
        "show_mod":True
    }
}