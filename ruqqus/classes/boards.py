from sqlalchemy import *
from sqlalchemy.orm import relationship, deferred
import time

from ruqqus.helpers.base36 import *
from ruqqus.helpers.security import *
from ruqqus.helpers.lazy import *
import ruqqus.helpers.aws as aws
from .submission import *
from .board_relationships import *
from .mix_ins import *
from ruqqus.__main__ import Base, db, cache

class Board(Base, Stndrd, Age_times):

    __tablename__="boards"

    id=Column(Integer, primary_key=True)
    name=Column(String)
    created_utc=Column(Integer)
    description = Column(String)
    description_html=Column(String)
    over_18=Column(Boolean, default=False)
    is_banned=Column(Boolean, default=False)
    has_banner=Column(Boolean, default=False)
    has_profile=Column(Boolean, default=False)
    creator_id=Column(Integer, ForeignKey("users.id"))
    ban_reason=Column(String(256), default=None)
    color=Column(String(8), default="603abb")

    moderators=relationship("ModRelationship", lazy="dynamic")
    subscribers=relationship("Subscription", lazy="dynamic")
    submissions=relationship("Submission", lazy="dynamic", backref="board", primaryjoin="Board.id==Submission.board_id")
    trending_rank=deferred(Column(Float, server_default=FetchedValue()))

    #db side functions
    subscriber_count=deferred(Column(Integer, server_default=FetchedValue()))
    
    def __init__(self, **kwargs):

        kwargs["created_utc"]=int(time.time())

        super().__init__(**kwargs)

    def __repr__(self):
        return f"Board(name={self.name})>"

    @property
    @lazy
    def base36id(self):
        return base36encode(self.id)
    
    @property
    @cache.memoize(timeout=30)
    def mods_list(self):

        z= [x for x in self.moderators.filter_by(accepted=True).order_by(text("id asc")).all()]
        return z

    @property
    @cache.memoize(timeout=30)
    def mods(self):

        z= [x.user for x in self.moderators.filter_by(accepted=True).order_by(text("id asc")).all()]
        return z

    @property
    @cache.memoize(timeout=30)
    def invited_mods(self):
        
        z=[x.user for x in self.moderators.filter_by(accepted=False, invite_rescinded=False).order_by(text("id")).all()]
        return z

    @property
    def permalink(self):

        return f"/+{self.name}"

    def can_take(self, post):
        return self.postrels.filter_by(post_id=post.id).first()

    @cache.memoize(timeout=600)
    def idlist(self, sort="hot", page=1, nsfw=False):

        posts=db.query(Submission).filter_by(is_banned=False,
                                             is_deleted=False,
                                             stickied=False,
                                             board_id=self.id
                                             )

        if not nsfw:
            posts=posts.filter_by(over_18=False)

        if sort=="hot":
            posts=posts.order_by(text("submissions.rank_hot desc"))
        elif sort=="new":
            posts=posts.order_by(Submission.created_utc.desc())
        elif sort=="disputed":
            posts=posts.order_by(text("submissions.rank_fiery desc"))
        elif sort=="top":
            posts=posts.order_by(text("submissions.score desc"))
        elif sort=="activity":
            posts=posts.order_by(text("submissions.rank_activity desc"))
        else:
            abort(422)

        posts=[x.id for x in posts.offset(25*(page-1)).limit(26).all()]

        return posts

    def rendered_board_page(self, v, sort="hot", page=1):

        if self.is_banned:
            if not (v and v.admin_level>=3):
                return render_template("board_banned.html", v=v, b=self)
        
        ids=self.idlist(sort=sort, page=page, nsfw=(v and v.over_18))

        next_exists=(len(ids)==26)
        ids=ids[0:25]

        if ids:

            #assemble list of tuples
            i=1
            tups=[]
            for x in ids:
                tups.append((x,i))
                i+=1

            tups=str(tups).lstrip("[").rstrip("]")

            #hit db for entries
            posts=db.query(Submission
                           ).from_statement(
                               text(
                               f"""
                                select submissions.*, submissions.ups, submissions.downs
                                from submissions
                                join (values {tups}) as x(id, n) on submissions.id=x.id
                                order by x.n"""
                               )).all()
        else:
            posts=[]

        
        is_subscribed=(v and self.has_subscriber(v))

        return render_template("board.html",
                               b=self,
                               v=v,
                               listing=posts,
                               next_exists=next_exists,
                               sort_method=sort,
                               page=page,
                               is_subscribed=is_subscribed)        


    @property
    def age_string(self):

        age=int(time.time()) - self.created_utc

        if age<60:
            return "just now"
        elif age<3600:
            minutes=int(age/60)
            return f"{minutes} minute{'s' if minutes>1 else ''} ago"
        elif age<86400:
            hours=int(age/3600)
            return f"{hours} hour{'s' if hours>1 else ''} ago"
        elif age<2592000:
            days=int(age/86400)
            return f"{days} day{'s' if days>1 else ''} ago"

        now=time.gmtime()
        ctd=time.gmtime(self.created_utc)
        months=now.tm_mon-ctd.tm_mon+12*(now.tm_year-ctd.tm_year)

        if months < 12:
            return f"{months} month{'s' if months>1 else ''} ago"
        else:
            years=int(months/12)
            return f"{years} year{'s' if years>1 else ''} ago"

    def has_mod(self, user):

        if user is None:
            return None

        return self.moderators.filter_by(user_id=user.id, accepted=True).first()


    @cache.memoize(timeout=60)
    def can_invite_mod(self, user):

        return user.id not in [x.user_id for x in self.moderators.filter_by(invite_rescinded=False).all()]

    def has_rescinded_invite(self, user):

        return user.id in [x.user_id for x in self.moderators.filter_by(invite_rescinded=True).all()]

    def has_invite(self, user):

        if user is None:
            return None

        return self.moderators.filter_by(user_id=user.id, accepted=False, invite_rescinded=False).first()
        
    def has_ban(self, user):

        if user is None:
            return None

        return db.query(BanRelationship).filter_by(board_id=self.id, user_id=user.id, is_active=True).first()

    def has_subscriber(self, user):

        if not user:
            return False

        return bool(self.subscribers.filter_by(board_id=self.id, user_id=user.id, is_active=True).first())


    def set_profile(self, file):

        aws.upload_file(name=f"board/{self.name.lower()}/profile.png",
                        file=file)
        self.has_profile=True
        db.add(self)
        db.commit()
        
    def set_banner(self, file):

        aws.upload_file(name=f"board/{self.name.lower()}/banner.png",
                        file=file)

        self.has_banner=True
        db.add(self)
        db.commit()

    def del_profile(self):

        aws.delete_file(name=f"board/{self.name.lower()}/profile.png")
        self.has_profile=False
        db.add(self)
        db.commit()

    def del_banner(self):

        aws.delete_file(name=f"board/{self.name.lower()}/banner.png")
        self.has_banner=False
        db.add(self)
        db.commit()

    @property
    def banner_url(self):

        if self.has_banner:
            return f"https://s3.us-east-2.amazonaws.com/i.ruqqus.com/board/{self.name.lower()}/banner.png"
        else:
            return "/assets/images/guilds/default-guild-banner.png"

    @property
    def profile_url(self):

        if self.has_profile:
            return f"https://s3.us-east-2.amazonaws.com/i.ruqqus.com/board/{self.name.lower()}/profile.png"
        else:
            return "/assets/images/guilds/default-guild-icon.png"

    @property
    def css_url(self):
        return f"{self.permalink}/css.css"
