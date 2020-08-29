from werkzeug.security import generate_password_hash, check_password_hash
from flask import *
import time
from sqlalchemy import *
from sqlalchemy.orm import relationship, deferred, joinedload, lazyload, contains_eager
from os import environ
from secrets import token_hex
import random
import pyotp

from ruqqus.helpers.base36 import *
from ruqqus.helpers.security import *
from ruqqus.helpers.lazy import lazy
import ruqqus.helpers.aws as aws
#from ruqqus.helpers.alerts import send_notification
from .votes import Vote
from .alts import Alt
from .titles import Title
from .submission import Submission
from .comment import Comment, Notification
from .boards import Board
from .board_relationships import *
from .mix_ins import *
from .subscriptions import *
from .userblock import *
from .badges import *
from .clients import *
from ruqqus.__main__ import Base,cache


class User(Base, Stndrd, Age_times):

    __tablename__="users"
    id = Column(Integer, primary_key=True)
    username = Column(String, default=None)
    email = Column(String, default=None)
    passhash = deferred(Column(String, default=None))
    created_utc = Column(Integer, default=0)
    admin_level = Column(Integer, default=0)
    is_activated = Column(Boolean, default=False)
    over_18=Column(Boolean, default=False)
    creation_ip=Column(String, default=None)
    submissions=relationship("Submission", lazy="dynamic", primaryjoin="Submission.author_id==User.id", backref="author_rel")
    comments=relationship("Comment", lazy="dynamic", primaryjoin="Comment.author_id==User.id")
    votes=relationship("Vote", lazy="dynamic", backref="users")
    commentvotes=relationship("CommentVote", lazy="dynamic", backref="users")
    bio=Column(String, default="")
    bio_html=Column(String, default="")
    badges=relationship("Badge", lazy="dynamic", backref="user")
    real_id=Column(String, default=None)
    notifications=relationship("Notification", lazy="dynamic", backref="user")
    referred_by=Column(Integer, default=None)
    is_banned=Column(Integer, default=0)
    unban_utc=Column(Integer, default=0)
    ban_reason=Column(String, default="")
    feed_nonce=Column(Integer, default=0)
    login_nonce=Column(Integer, default=0)
    title_id=Column(Integer, ForeignKey("titles.id"), default=None)
    title=relationship("Title", lazy="joined")
    has_profile=Column(Boolean, default=False)
    has_banner=Column(Boolean, default=False)
    reserved=Column(String(256), default=None)
    is_nsfw=Column(Boolean, default=False)
    tos_agreed_utc=Column(Integer, default=0)
    profile_nonce=Column(Integer, default=0)
    banner_nonce=Column(Integer, default=0)
    last_siege_utc=Column(Integer, default=0)
    mfa_secret=deferred(Column(String(16), default=None))
    hide_offensive=Column(Boolean, default=False)
    show_nsfl=Column(Boolean, default=False)
    is_private=Column(Boolean, default=False)
    read_announcement_utc=Column(Integer, default=0)
    #discord_id=Column(Integer, default=None)
    unban_utc=Column(Integer, default=0)
    is_deleted=Column(Boolean, default=False)
    delete_reason=Column(String(500), default='')
    filter_nsfw=Column(Boolean, default=False)

    patreon_id=Column(String(64), default=None)
    patreon_access_token=Column(String(128), default='')
    patreon_refresh_token=Column(String(128), default='')
    patreon_pledge_cents=Column(Integer, default=0)
    patreon_name=Column(String(64), default='')

    moderates=relationship("ModRelationship", lazy="dynamic")
    banned_from=relationship("BanRelationship", primaryjoin="BanRelationship.user_id==User.id")
    subscriptions=relationship("Subscription", lazy="dynamic")
    boards_created=relationship("Board", lazy="dynamic")
    contributes=relationship("ContributorRelationship", lazy="dynamic", primaryjoin="ContributorRelationship.user_id==User.id")
    board_blocks=relationship("BoardBlock", lazy="dynamic")

    following=relationship("Follow", primaryjoin="Follow.user_id==User.id")
    followers=relationship("Follow", primaryjoin="Follow.target_id==User.id")

    blocking=relationship("UserBlock", lazy="dynamic", primaryjoin="User.id==UserBlock.user_id")
    blocked=relationship("UserBlock", lazy="dynamic", primaryjoin="User.id==UserBlock.target_id")

    _applications = relationship("OauthApp", lazy="dynamic")

    #properties defined as SQL server-side functions
    energy = deferred(Column(Integer, server_default=FetchedValue()))
    comment_energy = deferred(Column(Integer, server_default=FetchedValue()))
    referral_count=deferred(Column(Integer, server_default=FetchedValue()))
    follower_count=deferred(Column(Integer, server_default=FetchedValue()))



    def __init__(self, **kwargs):

        if "password" in kwargs:

            kwargs["passhash"]=self.hash_password(kwargs["password"])
            kwargs.pop("password")

        kwargs["created_utc"]=int(time.time())

        super().__init__(**kwargs)


    def has_block(self, target):

        return g.db.query(UserBlock).filter_by(user_id=self.id, target_id=target.id).first()

    def is_blocked_by(self, user):

        return g.db.query(UserBlock).filter_by(user_id=user.id, target_id=self.id).first()

    def any_block_exists(self, other):

        return g.db.query(UserBlock).filter(or_(and_(UserBlock.user_id==self.id, UserBlock.target_id==other.id),and_(UserBlock.user_id==other.id, UserBlock.target_id==self.id))).first()
        
    def has_blocked_guild(self, board):

        return g.db.query(BoardBlock).filter_by(user_id=self.id, board_id=board.id).first()


    def validate_2fa(self, token):
        
        x=pyotp.TOTP(self.mfa_secret)
        return x.verify(token, valid_window=1)
    
    @property
    def boards_subscribed(self):

        boards= [x.board for x in self.subscriptions if x.is_active and not x.board.is_banned]
        return boards

    @property
    def age(self):
        return int(time.time())-self.created_utc
        
    @cache.memoize(timeout=300)
    def idlist(self, sort="hot", page=1, t=None, **kwargs):

        

        posts=g.db.query(Submission.id).options(lazyload('*')).filter_by(is_banned=False,
                                             is_deleted=False,
                                             stickied=False
                                             )


        if not self.over_18:
            posts=posts.filter_by(over_18=False)

        if self.hide_offensive:
            posts = posts.filter_by(is_offensive=False)

        if not self.show_nsfl:
            posts = posts.filter_by(is_nsfl=False)

        board_ids=g.db.query(Subscription.board_id).filter_by(user_id=self.id, is_active=True).subquery()
        user_ids =g.db.query(Follow.user_id).filter_by(user_id=self.id).join(Follow.target).filter(User.is_private==False).subquery()
        
        posts=posts.filter(
            or_(
                Submission.board_id.in_(board_ids),
                Submission.author_id.in_(user_ids)
                )
            )

        if self.admin_level < 4:
            #admins can see everything

            m=g.db.query(ModRelationship.board_id).filter_by(user_id=self.id, invite_rescinded=False).subquery()
            c=g.db.query(ContributorRelationship.board_id).filter_by(user_id=self.id).subquery()
            posts=posts.filter(
              or_(
                Submission.author_id==self.id,
                Submission.post_public==True,
                Submission.board_id.in_(m),
                Submission.board_id.in_(c)
                )
              )

            blocking=g.db.query(UserBlock.target_id).filter_by(user_id=self.id).subquery()
            blocked= g.db.query(UserBlock.user_id).filter_by(target_id=self.id).subquery()

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

        return [x[0] for x in posts.offset(25*(page-1)).limit(26).all()]

    @cache.memoize(300)
    def userpagelisting(self, v=None, page=1):

        submissions=g.db.query(Submission.id).options(lazyload('*')).filter_by(author_id=self.id)

        if not (v and v.over_18):
            submissions=submissions.filter_by(over_18=False)

        if v and v.hide_offensive:
            submissions=submissions.filter_by(is_offensive=False)

        if not (v and (v.admin_level >=3)):
            submissions=submissions.filter_by(is_deleted=False)

        if not (v and (v.admin_level >=3 or v.id==self.id)):
            submissions=submissions.filter_by(is_banned=False)

        if v and v.admin_level >=4:
            pass
        elif v:
            m=g.db.query(ModRelationship.board_id).filter_by(user_id=v.id, invite_rescinded=False).subquery()
            c=g.db.query(ContributorRelationship.board_id).filter_by(user_id=v.id).subquery()
            submissions=submissions.filter(
              or_(
                Submission.author_id==v.id,
                Submission.post_public==True,
                Submission.board_id.in_(m),
                Submission.board_id.in_(c)
                )
              )
        else:
            submissions=submissions.filter(Submission.post_public==True)

        listing = [x[0] for x in submissions.order_by(Submission.created_utc.desc()).offset(25*(page-1)).limit(26)]

        return listing

    @cache.memoize(300)
    def commentlisting(self, v=None, page=1):
        comments=self.comments.filter(Comment.parent_submission is not None).join(Comment.post)

        if not (v and v.over_18):
            comments=comments.filter_by(over_18=False)

        if v and v.hide_offensive:
            comments=comments.filter_by(is_offensive=False)

        if v and not v.show_nsfl:
            comments=comments.filter_by(is_nsfl=False)

        if (not v) or v.admin_level<3:
            comments=comments.filter_by(is_deleted=False)
            
        if not (v and (v.admin_level >=3 or v.id==self.id)):
            comments=comments.filter_by(is_banned=False)

        if v and v.admin_level >= 4:
            pass
        elif v:
            m=v.moderates.filter_by(invite_rescinded=False).subquery()
            c=v.contributes.subquery()
            
            comments=comments.join(m,
                                   m.c.board_id==Comment.board_id,
                                   isouter=True
                         ).join(c,
                                c.c.board_id==Comment.board_id,
                                isouter=True
                                )
            comments=comments.filter(or_(Comment.author_id==v.id,
                                   Comment.is_public==True,
                               m.c.board_id != None,
                               c.c.board_id !=None))
        else:
            comments=comments.filter(Submission.post_public==True)

        comments=comments.options(contains_eager(Comment.post))

        comments=comments.order_by(Comment.created_utc.desc())
        comments=comments.offset(25*(page-1)).limit(26)
        

        listing=[c.id for c in comments]
        return listing

    @property
    @lazy
    def mods_anything(self):

        return bool(self.moderates.filter_by(accepted=True).first())


    @property
    def boards_modded(self):

        z=[x.board for x in self.moderates if x and x.board and x.accepted and not x.board.is_banned]
        z=sorted(z, key=lambda x: x.name)

        return z

    @property
    @cache.memoize(timeout=3600) #1hr cache time for user rep
    def karma(self):
        return int(self.energy) - self.post_count

    @property
    @cache.memoize(timeout=3600)
    def comment_karma(self):
        return int(self.comment_energy) - self.comments.filter(Comment.parent_submission!=None).filter_by(is_banned=False).count()

    @property
    @cache.memoize(timeout=3600)
    def true_score(self):
        return max((self.karma + self.comment_karma), -5)


    @property
    def base36id(self):
        return base36encode(self.id)

    @property
    def fullname(self):
        return f"t1_{self.base36id}"

    @property
    @cache.memoize(timeout=60)
    def has_report_queue(self):
        board_ids=[x.board_id for x in self.moderates.filter_by(accepted=True).all()]
        return bool(g.db.query(Submission).filter(Submission.board_id.in_(board_ids), Submission.mod_approved==0, Submission.is_banned==False).join(Submission.reports).first())

    @property
    def banned_by(self):

        if not self.is_banned:
            return None

        return g.db.query(User).filter_by(id=self.is_banned).first()

    def has_badge(self, badgedef_id):
        return self.badges.filter_by(badge_id=badgedef_id).first()
    
    def vote_status_on_post(self, post):

        return post.voted


    def vote_status_on_comment(self, comment):

        return comment.voted
    

    def hash_password(self, password):
        return generate_password_hash(password, method='pbkdf2:sha512', salt_length=8)

    def verifyPass(self, password):
        return check_password_hash(self.passhash, password)

    @property
    def feedkey(self):

        return generate_hash(f"{self.username}{self.id}{self.feed_nonce}{self.created_utc}")





    @property
    def formkey(self):

        if "session_id" not in session:
            session["session_id"]=token_hex(16)

        msg=f"{session['session_id']}+{self.id}+{self.login_nonce}"

        return generate_hash(msg)

    def validate_formkey(self, formkey):

        return validate_hash(f"{session['session_id']}+{self.id}+{self.login_nonce}", formkey)
    
    @property
    def url(self):
        return f"/@{self.username}"

    @property
    def permalink(self):
        return self.url

    def __repr__(self):
        return f"<User(username={self.username})>"


    def notification_commentlisting(self, page=1, all_=False):

        notifications=self.notifications.join(Notification.comment).filter(
            Comment.is_banned==False, 
            Comment.is_deleted==False)

        if not all_:
            notifications=notifications.filter(Notification.read==False)

        notifications=notifications.options(
            contains_eager(Notification.comment)
            )

        notifications = notifications.order_by(Notification.id.desc()).offset(25*(page-1)).limit(26)

        output=[]
        for x in notifications:
            x.read=True
            g.db.add(x)
            output.append(x.comment_id)

        g.db.commit()
        return output


    
    @property
    def notifications_count(self):

        return self.notifications.filter_by(read=False).join(Notification.comment).filter(Comment.is_banned==False, Comment.is_deleted==False).count()

    @property
    def post_count(self):

        return self.submissions.filter_by(is_banned=False).count()

    @property
    def comment_count(self):

        return self.comments.filter(Comment.parent_submission!=None).filter_by(is_banned=False, is_deleted=False).count()

    @property
    #@cache.memoize(timeout=60)
    def badge_pairs(self):

        output=[]

        badges=[x for x in self.badges.all()]

        while badges:
            
            to_append=[badges.pop(0)]
            
            if badges:
                to_append.append(badges.pop(0))
                
            output.append(to_append)

        return output

    @property
    def alts(self):

        alts1=g.db.query(User).join(Alt, Alt.user2==User.id).filter(Alt.user1==self.id).all()
        alts2=g.db.query(User).join(Alt, Alt.user1==User.id).filter(Alt.user2==self.id).all()

        output= list(set([x for x in alts1]+[y for y in alts2]))
        output=sorted(output, key=lambda x: x.username)

        return output
        

    def has_follower(self, user):

        return g.db.query(Follow).filter_by(target_id=self.id, user_id=user.id).first()

    def set_profile(self, file):

        self.del_profile()
        self.profile_nonce+=1

        aws.upload_file(name=f"users/{self.username}/profile-{self.profile_nonce}.png",
                        file=file,
                        resize=(100,100)
                        )
        self.has_profile=True
        g.db.add(self)

    def set_banner(self, file):

        self.del_banner()
        self.banner_nonce+=1

        aws.upload_file(name=f"users/{self.username}/banner-{self.banner_nonce}.png",
                        file=file)

        self.has_banner=True
        g.db.add(self)
        

    def del_profile(self):

        aws.delete_file(name=f"users/{self.username}/profile-{self.profile_nonce}.png")
        self.has_profile=False
        g.db.add(self)
        

    def del_banner(self):

        aws.delete_file(name=f"users/{self.username}/banner-{self.banner_nonce}.png")
        self.has_banner=False
        g.db.add(self)
        

    @property
    def banner_url(self):

        if self.has_banner:
            return f"https://i.ruqqus.com/users/{self.username}/banner-{self.banner_nonce}.png"
        else:
            return "/assets/images/profiles/default_bg.png"

    @property
    def profile_url(self):

        if self.has_profile:
            return f"https://i.ruqqus.com/users/{self.username}/profile-{self.profile_nonce}.png"
        else:
            return "/assets/images/profiles/default-profile-pic.png"

    @property
    def available_titles(self):

        locs={"v":self,
              "Board":Board,
              "Submission":Submission
              }

        titles=[i for i in g.db.query(Title).order_by(text("id asc")).all() if eval(i.qualification_expr,{}, locs)]
        return titles

    @property
    def can_make_guild(self):
        return (self.true_score >= 250 or self.created_utc <= 1592974538 and self.true_score >= 50 or (self.patreon_pledge_cents and self.patreon_pledge_cents>=500)) and len(self.boards_modded) < 10
    
    @property
    def can_join_gms(self):
        return len(self.boards_modded) < 10
    

    @property
    def can_siege(self):

        if self.is_banned:
            return False

        now=int(time.time())

        return now - max(self.last_siege_utc, self.created_utc) > 60*60*24*30

    @property
    def can_submit_image(self):
        return (self.patreon_pledge_cents and self.patreon_pledge_cents>=500) or self.true_score >= 1000 or (self.created_utc <= 1592974538 and self.true_score >= 500)

    @property
    def can_upload_avatar(self):
        return self.patreon_pledge_cents or self.true_score >= 300 or self.created_utc <= 1592974538

    @property
    def can_upload_banner(self):
        return self.patreon_pledge_cents or self.true_score >= 500 or self.created_utc <= 1592974538

    @property
    def json(self):

        if self.is_banned:
            return {'username':self.username,
                    'permalink':self.permalink,
                    'is_banned':True,
                    'ban_reason':self.ban_reason,
                    'id':self.base36id
                    }

        elif self.is_deleted:
            return {'username':self.username,
                    'permalink':self.permalink,
                    'is_deleted':True,
                    'id':self.base36id
                    }

        return {'username':self.username,
                'permalink':self.permalink,
                'is_banned':False,
                'created_utc':self.created_utc,
                'post_rep':int(self.karma),
                'comment_rep':int(self.comment_karma),
                'badges':[x.json for x in self.badges],
                'id':self.base36id,
                'profile_url':self.profile_url,
                'banner_url':self.banner_url,
                'post_count':self.post_count,
                'comment_count':self.comment_count,
                'title':self.title.json if self.title else None,
                'bio':self.bio,
                'bio_html':self.bio_html
                }

    @property
    def total_karma(self):

        return max(self.karma+self.comment_karma, -5)

    @property        
    def can_use_darkmode(self):
        return True
        #return self.referral_count or self.has_earned_darkmode or self.has_badge(16) or self.has_badge(17)


    def ban(self, admin=None, reason=None, include_alts=True, days=0):

        if days > 0:
            ban_time = int(time.time()) + (days * 86400)
            self.unban_utc = ban_time

        else:
            #Takes care of all functions needed for account termination
            self.unban_utc=0
            if self.has_banner:
                self.del_banner()
            if self.has_profile:
                self.del_profile()

        self.is_banned=admin.id if admin else 1
        if reason:
            self.ban_reason=reason

        g.db.add(self)
        

        if include_alts:
            for alt in self.alts:

                if alt.is_banned:
                    continue

                # suspend alts
                if days:
                    alt.ban(admin=admin, reason=reason, include_alts=False, days=days)

                # ban alts
                else:
                    alt.ban(admin=admin, include_alts=False)

    def unban(self, include_alts=False):

        #Takes care of all functions needed for account reinstatement.

        self.is_banned=0
        self.unban_utc=0

        g.db.add(self)
        

        if include_alts:
            for alt in self.alts:
                # ban alts
                alt.unban()

    @property
    def is_suspended(self):
        return  (self.is_banned and (self.unban_utc == 0 or self.unban_utc > time.time()))


    @property
    def is_blocking(self):
        return self.__dict__.get('_is_blocking', 0)

    @property
    def is_blocked(self):
        return self.__dict__.get('_is_blocked', 0)   

    def refresh_selfset_badges(self):

        #check self-setting badges
        badge_types = g.db.query(BadgeDef).filter(BadgeDef.qualification_expr.isnot(None)).all()
        for badge in badge_types:
            if eval(badge.qualification_expr, {}, {'v':self}):
                if not self.has_badge(badge.id):
                    new_badge=Badge(user_id=self.id,
                                    badge_id=badge.id,
                                    created_utc=int(time.time())
                                    )
                    g.db.add(new_badge)
                    
            else:
                bad_badge=self.has_badge(badge.id)
                if bad_badge:
                    g.db.delete(bad_badge)

        g.db.add(self)

    @property
    def applications(self):
        return [x for x in self._applications.order_by(OauthApp.id.asc()).all()]