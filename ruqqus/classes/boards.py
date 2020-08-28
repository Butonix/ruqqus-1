from sqlalchemy import *
from sqlalchemy.orm import relationship, deferred, lazyload
import time

from ruqqus.helpers.base36 import *
from ruqqus.helpers.security import *
from ruqqus.helpers.lazy import *
from ruqqus.helpers.session import *
import ruqqus.helpers.aws as aws
from .userblock import *
from .submission import *
from .subscriptions import *
from .board_relationships import *
from .comment import Comment
from .mix_ins import *
from ruqqus.__main__ import Base, cache

class Board(Base, Stndrd, Age_times):

    __tablename__="boards"

    id=Column(Integer, primary_key=True)
    name=Column(String)
    created_utc=Column(Integer)
    description = Column(String)
    description_html=Column(String)
    over_18=Column(Boolean, default=False)
    is_nsfl=Column(Boolean, default=False)
    is_banned=Column(Boolean, default=False)
    has_banner=Column(Boolean, default=False)
    has_profile=Column(Boolean, default=False)
    creator_id=Column(Integer, ForeignKey("users.id"))
    ban_reason=Column(String(256), default=None)
    color=Column(String(8), default="805ad5")
    restricted_posting=Column(Boolean, default=False)
    hide_banner_data=Column(Boolean, default=False)
    profile_nonce=Column(Integer, default=0)
    banner_nonce=Column(Integer, default=0)
    is_private=Column(Boolean, default=False)
    color_nonce=Column(Integer, default=0)
    rank_trending=Column(Float, default=0)
    stored_subscriber_count=Column(Integer, default=1)
    all_opt_out=Column(Boolean, default=False)

    moderators=relationship("ModRelationship")
    subscribers=relationship("Subscription", lazy="dynamic")
    submissions=relationship("Submission", primaryjoin="Board.id==Submission.board_id")
    contributors=relationship("ContributorRelationship", lazy="dynamic")
    bans=relationship("BanRelationship", lazy="dynamic")
    postrels=relationship("PostRelationship", lazy="dynamic")
    trending_rank=deferred(Column(Float, server_default=FetchedValue()))

    #db side functions
    subscriber_count=deferred(Column(Integer, server_default=FetchedValue()))
    
    def __init__(self, **kwargs):

        kwargs["created_utc"]=int(time.time())

        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Board(name={self.name})>"

    @property
    def fullname(self):
        return f"t4_{self.base36id}"
    
    
    @property
    def mods_list(self):

        z= [x for x in self.moderators if x.accepted and not (x.user.is_deleted or (x.user.is_banned and not x.user.unban_utc))]

        z=sorted(z, key=lambda x: x.id)
        return z

    @property
    def mods(self):

        z= [x.user for x in self.moderators if x.accepted]

        z=sorted(z, key=lambda x: x.id)

        return z

    @property
    def invited_mods(self):
        
        z=[x.user for x in self.moderators if x.accepted==False and x.invite_rescinded==False]
        z=sorted(z, key=lambda x: x.id)
        return z

    @property
    def mods_count(self):

        return len([x for x in self.moderators if x.accepted and not x.invite_rescinded])

    @property
    def permalink(self):

        return f"/+{self.name}"

    def can_take(self, post):
        if self.is_banned:
            return False
        return not self.postrels.filter_by(post_id=post.id).first()

    @cache.memoize(timeout=60)
    def idlist(self, sort="hot", page=1, t=None, show_offensive=True, v=None, nsfw=False, **kwargs):

        posts=g.db.query(Submission.id).options(lazyload('*')).filter_by(is_banned=False,
                                         is_deleted=False,
                                         is_pinned=False,
                                         board_id=self.id
                                        )

        if not nsfw:
            posts=posts.filter_by(over_18=False)

        if v and v.hide_offensive:
            posts = posts.filter_by(is_offensive=False)

        if v and not v.show_nsfl:
            posts = posts.filter_by(is_nsfl=False)

        if self.is_private:
            if v and (self.can_view(v) or v.admin_level >= 4):
                pass
            elif v:
                posts=posts.filter(or_(Submission.post_public==True,
                                       Submission.author_id==v.id
                                       )
                                   )
            else:
                posts=posts.filter_by(post_public=True)

        if v and not self.has_mod(v) and v.admin_level<=3:
            #blocks
            blocking=g.db.query(UserBlock.target_id).filter_by(user_id=v.id).subquery()
            blocked= g.db.query(UserBlock.user_id).filter_by(target_id=v.id).subquery()

            posts=posts.filter(
                Submission.author_id.notin_(blocking),
                Submission.author_id.notin_(blocked)
                )


        if t:
            now=int(time.time())
            if t=='day':
                cutoff=now-86400
            elif t=='week':
                cutoff=now-604800
            elif t=='month':
                cutoff=now-2592000
            elif t=='year':
                cutoff=now-31536000
            else:
                cutoff=0
            posts=posts.filter(Submission.created_utc >= cutoff)
            

        if sort=="hot":
            posts=posts.order_by(Submission.score_best.desc())
        elif sort=="new":
            posts=posts.order_by(Submission.created_utc.desc())
        elif sort=="disputed":
            posts=posts.order_by(Submission.score_disputed.desc())
        elif sort=="top":
            posts=posts.order_by(Submission.score_top.desc())
        elif sort=="activity":
            posts=posts.order_by(Submission.score_activity.desc())
        else:
            abort(422)

        posts=[x[0] for x in posts.offset(25*(page-1)).limit(26).all()]

        return posts

    def has_mod(self, user):

        if user is None:
            return None

        if self.is_banned:
            return False

        for x in user.moderates:
            if x.board_id==self.id and x.accepted and not x.invite_rescinded:
                return x

        return False


    def can_invite_mod(self, user):

        return user.id not in [x.user_id for x in self.moderators if not x.invite_rescinded]

    def has_rescinded_invite(self, user):

        return user.id in [x.user_id for x in self.moderators if x.invite_rescinded==True]

    def has_invite(self, user):

        if user is None:
            return None

        for x in [i for i in self.moderators if not i.invite_rescinded and not i.accepted]:

            if x.user_id==user.id:
                return x

        return None
        
    def has_ban(self, user):

        if user is None:
            return None

        return g.db.query(BanRelationship).filter_by(board_id=self.id, user_id=user.id, is_active=True).first()

    def has_subscriber(self, user):

        if not user:
            return False

        return self.id in [x.board_id for x in user.subscriptions.all() if x.is_active]

    def has_contributor(self, user):

        if user is None:
            return False

        return g.db.query(ContributorRelationship).filter_by(user_id=user.id, is_active=True).first()

    def can_submit(self, user):

        if user is None:
            return False

        if user.admin_level >= 4:
            return True

        if self.has_ban(user):
            return False

        if self.has_contributor(user) or self.has_mod(user):
            return True

        if self.is_private or self.restricted_posting:
            return False

        return True

    def can_comment(self, user):

        if user is None:
            return False

        if user.admin_level >= 4:
            return True

        if self.has_ban(user):
            return False

        if self.has_contributor(user) or self.has_mod(user):
            return True

        if self.is_private:
            return False

        return True

    def can_view(self, user):

        if user is None:
            return False

        if user.admin_level >=4:
            return True

        if self.has_contributor(user) or self.has_mod(user) or self.has_invite(user):
            return True

        if self.is_private:
            return False

        

    def set_profile(self, file):

        self.del_profile()
        self.profile_nonce+=1

        aws.upload_file(name=f"board/{self.name.lower()}/profile-{self.profile_nonce}.png",
                        file=file,
                        resize=(100,100)
                        )
        self.has_profile=True
        g.db.add(self)
        
        
    def set_banner(self, file):

        self.del_banner()
        self.banner_nonce+=1

        aws.upload_file(name=f"board/{self.name.lower()}/banner-{self.banner_nonce}.png",
                        file=file)

        self.has_banner=True
        g.db.add(self)
        

    def del_profile(self):

        aws.delete_file(name=f"board/{self.name.lower()}/profile-{self.profile_nonce}.png")
        self.has_profile=False
        g.db.add(self)
        

    def del_banner(self):

        aws.delete_file(name=f"board/{self.name.lower()}/banner-{self.banner_nonce}.png")
        self.has_banner=False
        g.db.add(self)
        

    @property
    def banner_url(self):

        if self.has_banner:
            return f"https://i.ruqqus.com/board/{self.name.lower()}/banner-{self.banner_nonce}.png"
        else:
            return "/assets/images/guilds/default-guild-banner.png"

    @property
    def profile_url(self):

        if self.has_profile:
            return f"https://i.ruqqus.com/board/{self.name.lower()}/profile-{self.profile_nonce}.png"
        else:
            if self.over_18:
                return "/assets/images/icons/nsfw_guild_icon.png"
            else:
                return "/assets/images/guilds/default-guild-icon.png"

    @property
    def css_url(self):
        return f"/assets/{self.name}/main/{self.color_nonce}.css"

    @property
    def css_dark_url(self):
        return f"/assets/{self.name}/dark/{self.color_nonce}.css"


    def has_participant(self, user):
        return (g.db.query(Submission).filter_by(original_board_id=self.id, author_id=user.id).first() or
                g.db.query(Comment).filter_by(author_id=user.id, original_board_id=self.id).first()
                )
    @property
    @lazy
    def n_pins(self):
        return g.db.query(Submission).filter_by(board_id=self.id, is_pinned=True).count()

    @property
    def can_pin_another(self):

        return self.n_pins < 4

    @property
    def json(self):

        if self.is_banned:
            return {'name':self.name,
                    'permalink':self.permalink,
                    'is_banned':True,
                    'ban_reason':self.ban_reason,
                    'id':self.base36id
                    }
        return {'name':self.name,
                'profile_url':self.profile_url,
                'banner_url':self.banner_url,
                'created_utc':self.created_utc,
                'mods_count':self.mods_count,
                'subscriber_count':self.subscriber_count,
                'permalink':self.permalink,
                'description':self.description,
                'description_html':self.description_html,
                'over_18':self.over_18,
                'is_banned':False,
                'is_private':self.is_private,
                'is_restricted':self.restricted_posting,
                'id':self.base36id,
                'fullname':self.fullname,
                'banner_url':self.banner_url,
                'profile_url':self.profile_url,
                'color':"#"+self.color
                }

