from flask import *
import time
from sqlalchemy import *
from sqlalchemy.orm import relationship, deferred
from sqlalchemy.ext.associationproxy import association_proxy
from random import randint
import math
from .mix_ins import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.lazy import lazy
from ruqqus.__main__ import Base, cache
from .votes import CommentVote
from .flags import CommentFlag
from .badwords import *


class CommentAux(Base):

    __tablename__ = "comments_aux"

    key_id = Column(Integer, primary_key=True)
    id = Column(Integer, ForeignKey("comments.id"))
    body = Column(String(10000), default=None)
    body_html = Column(String(20000))
    ban_reason = Column(String(256), default='')


class Comment(Base, Age_times, Scores, Stndrd, Fuzzing):

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    comment_aux = relationship(
        "CommentAux",
        lazy="joined",
        uselist=False,
        innerjoin=True,
        primaryjoin="Comment.id==CommentAux.id")
    author_id = Column(Integer, ForeignKey("users.id"))
    parent_submission = Column(Integer, ForeignKey("submissions.id"))
    # this column is foreignkeyed to comment(id) but we can't do that yet as
    # "comment" class isn't yet defined
    parent_fullname = Column(Integer)
    created_utc = Column(Integer, default=0)
    edited_utc = Column(Integer, default=0)
    is_banned = Column(Boolean, default=False)
    distinguish_level = Column(Integer, default=0)
    gm_distinguish = Column(Integer, ForeignKey("boards.id"), default=0)
    distinguished_board = relationship("Board", lazy="joined", primaryjoin="Comment.gm_distinguish==Board.id")
    is_deleted = Column(Boolean, default=False)
    is_approved = Column(Integer, default=0)
    approved_utc = Column(Integer, default=0)
    creation_ip = Column(String(64), default='')
    score_disputed = Column(Float, default=0)
    score_hot = Column(Float, default=0)
    score_top = Column(Integer, default=1)
    level = Column(Integer, default=0)
    parent_comment_id = Column(Integer, ForeignKey("comments.id"))
    original_board_id = Column(Integer, ForeignKey("boards.id"))

    over_18 = Column(Boolean, default=False)
    is_op = Column(Boolean, default=False)
    is_offensive = Column(Boolean, default=False)
    is_nsfl = Column(Boolean, default=False)
    is_bot = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)

    app_id = Column(Integer, ForeignKey("oauth_apps.id"), default=None)
    oauth_app=relationship("OauthApp")

    post = relationship("Submission")
    flags = relationship("CommentFlag", backref="comment")
    author = relationship(
        "User",
        lazy="joined",
        innerjoin=True,
        primaryjoin="User.id==Comment.author_id")
    board = association_proxy("post", "board")
    original_board = relationship(
        "Board", primaryjoin="Board.id==Comment.original_board_id")

    upvotes = Column(Integer, default=1)
    downvotes = Column(Integer, default=0)

    parent_comment = relationship("Comment", remote_side=[id])
    child_comments = relationship("Comment", remote_side=[parent_comment_id])

    awards = relationship("AwardRelationship", lazy="joined")

    # These are virtual properties handled as postgres functions server-side
    # There is no difference to SQLAlchemy, but they cannot be written to
    ups = deferred(Column(Integer, server_default=FetchedValue()))
    downs = deferred(Column(Integer, server_default=FetchedValue()))
    is_public = deferred(Column(Boolean, server_default=FetchedValue()))

    score = deferred(Column(Integer, server_default=FetchedValue()))

    rank_fiery = deferred(Column(Float, server_default=FetchedValue()))
    rank_hot = deferred(Column(Float, server_default=FetchedValue()))

    #flag_count=deferred(Column(Integer, server_default=FetchedValue()))

    board_id = deferred(Column(Integer, server_default=FetchedValue()))

    def __init__(self, *args, **kwargs):

        if "created_utc" not in kwargs:
            kwargs["created_utc"] = int(time.time())

        kwargs["creation_ip"] = request.remote_addr

        super().__init__(*args, **kwargs)

    def __repr__(self):

        return f"<Comment(id={self.id})>"

    @property
    @lazy
    def fullname(self):
        return f"t3_{self.base36id}"

    @property
    @lazy
    def is_top_level(self):
        return self.parent_fullname and self.parent_fullname.startswith("t2_")

    @property
    def is_archived(self):
        return self.post.is_archived

    @property
    @lazy
    def parent(self):

        if not self.parent_submission:
            return None

        if self.is_top_level:
            return self.post

        else:
            return g.db.query(Comment).get(self.parent_comment_id)

    @property
    def children(self):

        return g.db.query(Comment).filter_by(parent_comment_id=self.id).all()

    @property
    def replies(self):

        r = self.__dict__.get("replies", None)
        if r is None:
            r = self.child_comments
        return r

    @replies.setter
    def replies(self, value):
        self.__dict__["replies"] = value

    @property
    @lazy
    def permalink(self):

        return f"{self.post.permalink}/{self.base36id}"

    @property
    def any_descendants_live(self):

        if self.replies == []:
            return False

        if any([not x.is_banned and not x.is_deleted for x in self.replies]):
            return True

        else:
            return any([x.any_descendants_live for x in self.replies])

    def rendered_comment(self, v=None, render_replies=True,
                         standalone=False, level=1, **kwargs):

        kwargs["post_base36id"] = kwargs.get(
            "post_base36id", self.post.base36id if self.post else None)

        if self.is_banned or self.is_deleted:
            if v and v.admin_level > 1:
                return render_template("single_comment.html",
                                       v=v,
                                       c=self,
                                       render_replies=render_replies,
                                       standalone=standalone,
                                       level=level,
                                       **kwargs)

            elif self.any_descendants_live:
                return render_template("single_comment_removed.html",
                                       c=self,
                                       render_replies=render_replies,
                                       standalone=standalone,
                                       level=level,
                                       **kwargs)
            else:
                return ""

        return render_template("single_comment.html",
                               v=v,
                               c=self,
                               render_replies=render_replies,
                               standalone=standalone,
                               level=level,
                               **kwargs)

    @property
    def active_flags(self):
        if self.is_approved:
            return 0
        else:
            return self.flag_count

    def visibility_reason(self, v):
        if self.author_id == v.id:
            return "this is your content."
        elif not self.board:
            return None
        elif self.board.has_mod(v):
            return f"you are a guildmaster of +{self.board.name}."
        elif self.board.has_contributor(v):
            return f"you are an approved contributor in +{self.board.name}."
        elif self.parent.author_id == v.id:
            return "this is a reply to your content."
        elif v.admin_level >= 4:
            return "you are a Ruqqus admin."

    def determine_offensive(self):

        for x in g.db.query(BadWord).all():
            if x.check(self.body):
                self.is_offensive = True

                break
        else:
            self.is_offensive = False

    @property
    def json_core(self):
        if self.is_banned:
            data= {'is_banned': True,
                    'ban_reason': self.ban_reason,
                    'id': self.base36id,
                    'post': self.post.base36id,
                    'level': self.level,
                    'parent': self.parent_fullname
                    }
        elif self.is_deleted:
            data= {'is_deleted': True,
                    'id': self.base36id,
                    'post': self.post.base36id,
                    'level': self.level,
                    'parent': self.parent_fullname
                    }
        else:
            data= {
                'id': self.base36id,
                'fullname': self.fullname,
                'level': self.level,
                'author_name': self.author.username if not self.author.is_deleted else None,
                'body': self.body,
                'body_html': self.body_html,
                'is_archived': self.is_archived,
                'is_bot': self.is_bot,
                'created_utc': self.created_utc,
                'edited_utc': self.edited_utc or 0,
                'is_banned': False,
                'is_deleted': False,
                'is_nsfw': self.over_18,
                'is_offensive': self.is_offensive,
                'is_nsfl': self.is_nsfl,
                'permalink': self.permalink,
                'post_id': self.post.base36id,
                'score': self.score_fuzzed,
                'upvotes': self.upvotes_fuzzed,
                'downvotes': self.downvotes_fuzzed,
                'award_count': self.award_count
                }

            if self.level>=2:
                data['parent_comment_id']= base36encode(self.parent_comment_id),


        return data

    @property
    def json(self):
    
        data=self.json_core

        if self.is_deleted or self.is_banned:
            return data

        data["author"]=self.author.json_core
        data["post"]=self.post.json_core
        data["guild"]=self.post.board.json_core

        if self.level >= 2:
            data["parent"]=self.parent.json_core

        if "replies" in self.__dict__:
            data['replies']=[x.json_core for x in self.replies]

        return data

        
    @property
    def voted(self):

        x = self.__dict__.get("_voted")
        if x is not None:
            return x

        if g.v:
            x = g.db.query(CommentVote).filter_by(
                comment_id=self.id,
                user_id=g.v.id
            ).first()

            if x:
                x = x.vote_type
            else:
                x = 0
        else:
            x = 0
        return x

    @property
    def title(self):
        return self.__dict__.get("_title", self.author.title)

    @property
    def is_blocking(self):
        return self.__dict__.get('_is_blocking', 0)

    @property
    def is_blocked(self):
        return self.__dict__.get('_is_blocked', 0)

    @property
    def body(self):
        return self.comment_aux.body

    @body.setter
    def body(self, x):
        self.comment_aux.body = x
        g.db.add(self.comment_aux)

    @property
    def body_html(self):
        return self.comment_aux.body_html

    @body_html.setter
    def body_html(self, x):
        self.comment_aux.body_html = x
        g.db.add(self.comment_aux)

    @property
    def ban_reason(self):
        return self.comment_aux.ban_reason

    @ban_reason.setter
    def ban_reason(self, x):
        self.comment_aux.ban_reason = x
        g.db.add(self.comment_aux)

    @property
    def flag_count(self):
        return len(self.flags)

    @property
    def award_count(self):
        return len(self.awards)

    def collapse_for_user(self, v):

        if not v:
            return False

        if self.is_offensive and v.hide_offensive:
            return True

        if any([x in self.body for x in v.filter_words]):
            return True

        return False

    @property
    def self_download_json(self):

        #This property should never be served to anyone but author and admin
        if not self.is_banned and not self.is_banned:
            return self.json_core

        data= {
            "author": self.author.name,
            "body": self.body,
            "body_html": self.body_html,
            "is_banned": bool(self.is_banned),
            "is_deleted": self.is_deleted,
            'created_utc': self.created_utc,
            'id': self.base36id,
            'fullname': self.fullname,
            'permalink': self.permalink,
            'post_id': self.post.base36id,
            'level': self.level
        }
        if self.level>=2:
            data['parent_comment_id']= base36encode(self.parent_comment_id)

        return data
    


class Notification(Base):

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    comment_id = Column(Integer, ForeignKey("comments.id"))
    read = Column(Boolean, default=False)

    comment = relationship("Comment", lazy="joined", innerjoin=True)
    user=relationship("User", innerjoin=True)

    # Server side computed values (copied from corresponding comment)
    created_utc = Column(Integer, server_default=FetchedValue())

    def __repr__(self):

        return f"<Notification(id={self.id})>"

    @property
    def voted(self):
        return 0
