from werkzeug.security import generate_password_hash, check_password_hash
from flask import *
import time
from sqlalchemy import *
from sqlalchemy.orm import relationship, deferred
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
from ruqqus.__main__ import Base, db, cache

class User(Base, Stndrd):

    __tablename__="users"
    id = Column(Integer, primary_key=True)
    username = Column(String, default=None)
    email = Column(String, default=None)
    passhash = Column(String, default=None)
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
    ban_reason=Column(String, default="")
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
    mfa_secret=Column(String(16), default=None)
    hide_offensive=Column(Boolean, default=False)
    show_nsfl=Column(Boolean, default=False)
    is_private=Column(Boolean, default=False)
    read_announcement_utc=Column(Integer, default=0)
    discord_id=Column(Integer, default=None)

    

    moderates=relationship("ModRelationship", lazy="dynamic")
    banned_from=relationship("BanRelationship", lazy="dynamic", primaryjoin="BanRelationship.user_id==User.id")
    subscriptions=relationship("Subscription", lazy="dynamic")
    boards_created=relationship("Board", lazy="dynamic")
    contributes=relationship("ContributorRelationship", lazy="dynamic", primaryjoin="ContributorRelationship.user_id==User.id")

    following=relationship("Follow", lazy="dynamic", primaryjoin="Follow.user_id==User.id")
    followers=relationship("Follow", lazy="dynamic", primaryjoin="Follow.target_id==User.id")


    
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
    def idlist(self, sort="hot", page=1, t=None, hide_offensive=False, **kwargs):

        

        posts=db.query(Submission).filter_by(is_banned=False,
                                             is_deleted=False,
                                             stickied=False
                                             )

        if not self.over_18:
            posts=posts.filter_by(over_18=False)

        if hide_offensive:
            posts = posts.filter_by(is_offensive=False)

        if not self.show_nsfl:
            posts = posts.filter_by(is_nsfl=False)

        board_ids=[x.board_id for x in self.subscriptions.filter_by(is_active=True).all()]
        user_ids =[x.target.id for x in self.following.all() if x.target.is_private==False]
        
        posts=posts.filter(
            or_(
                Submission.board_id.in_(board_ids),
                Submission.author_id.in_(user_ids)
                )
            )

        if not self.admin_level >=4:
            #admins can see everything
            m=self.moderates.filter_by(invite_rescinded=False).subquery()
            c=self.contributes.filter_by(is_active=True).subquery()
            posts=posts.join(m,
                             m.c.board_id==Submission.board_id,
                             isouter=True
                             ).join(c,
                                    c.c.board_id==Submission.board_id,
                                    isouter=True
                                    )
            posts=posts.filter(or_(Submission.author_id==self.id,
                                   Submission.is_public==True,
                                   m.c.board_id != None,
                                   c.c.board_id !=None))

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
            posts=posts.order_by(Submission.score_hot.desc())
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

        posts=[x.id for x in posts.offset(25*(page-1)).limit(26).all()]

        return posts

    def list_of_posts(self, ids):

        next_exists=(len(ids)==26)
        ids=ids[0:25]

        if ids:

##            #assemble list of tuples
##            i=1
##            tups=[]
##            for x in ids:
##                tups.append((x,i))
##                i+=1
##
##            tups=str(tups).lstrip("[").rstrip("]")
##
##            #hit db for entries
##            posts=db.query(Submission
##                           ).from_statement(
##                               text(
##                               f"""
##                                select submissions.*
##                                from submissions
##                                join (values {tups}) as x(id, n) on submissions.id=x.id
##                                where x.n is not null
##                                order by x.n"""
##                               )).all()
            posts=[]
            for x in ids:
                posts.append(db.query(Submission).filter_by(id=x).first())
            
        else:
            posts=[]

        return posts, next_exists

    @property
    def mods_anything(self):

        return bool(self.moderates.filter_by(accepted=True).first())


    @property
    def boards_modded(self):

        return [x.board for x in self.moderates.filter_by(accepted=True).all() if not x.board.is_banned]

    @property
    @cache.memoize(timeout=3600) #1hr cache time for user rep
    def karma(self):
        return int(self.energy)

    @property
    @cache.memoize(timeout=3600)
    def comment_karma(self):
        return int(self.comment_energy)


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
        return bool(db.query(Submission).filter(Submission.board_id.in_(board_ids), Submission.mod_approved==0, Submission.report_count>=1).first())

    @property
    def banned_by(self):

        if not self.is_banned:
            return None

        return db.query(User).filter_by(id=self.is_banned).first()

    def has_badge(self, badgedef_id):
        return self.badges.filter_by(badge_id=badgedef_id).first()
    
    def vote_status_on_post(self, post):

        vote = self.votes.filter_by(submission_id=post.id).first()
        if not vote:
            return 0
        
        return vote.vote_type


    def vote_status_on_comment(self, comment):

        vote = self.commentvotes.filter_by(comment_id=comment.id).first()
        if not vote:
            return 0
        
        return vote.vote_type
    

    def hash_password(self, password):
        return generate_password_hash(password, method='pbkdf2:sha512', salt_length=8)

    def verifyPass(self, password):
        return check_password_hash(self.passhash, password)

    def rendered_comments_page(self, v=None):
        if self.reserved:
            return render_template("userpage_reserved.html", u=self, v=v)

        if self.is_banned and (not v or v.admin_level < 3):
            return render_template("userpage_banned.html", u=self, v=v)

        if self.is_private and (not v or (v.id!=self.id and not v.admin_level<3)):
            return render_template("userpage_private.html", u=self, v=v)
        
        page=int(request.args.get("page","1"))

        comments=self.comments.filter(Comment.parent_submission is not None)

        if not (v and v.over_18):
            comments=comments.filter_by(over_18=False)

        if v and v.hide_offensive:
            comments=comments.filter_by(is_offensive=False)

        if v and v.hide_nsfl:
            comments=comments.filter_by(is_nsfl=False)

        if not (v and (v.admin_level >=3)):
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
            comments=comments.filter_by(is_public=True)

        comments=comments.order_by(Comment.created_utc.desc())
        comments=comments.offset(25*(page-1)).limit(26)
        

        listing=[c for c in comments]
        #we got 26 items just to see if a next page exists
        next_exists=(len(listing)==26)
        listing=listing[0:25]

        is_following=(v and self.has_follower(v))
        
        return render_template("userpage_comments.html",
                               u=self,
                               v=v,
                               listing=listing,
                               page=page,
                               next_exists=next_exists,
                               is_following=is_following)

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

    @property
    @lazy
    def created_date(self):

        return time.strftime("%d %B %Y", time.gmtime(self.created_utc))

    def __repr__(self):
        return f"<User(username={self.username})>"

    def notifications_page(self, page=1, include_read=False):

        page=int(page)

        notifications=self.notifications.filter_by(is_banned=False, is_deleted=False)

        if not include_read:
            notifications=notifications.filter_by(read=False)

        notifications = notifications.order_by(Notification.id.desc()).offset(25*(page-1)).limit(26)

        comments=[n.comment for n in notifications]
        next_exists=(len(comments)==26)
        comments=comments[0:25]

        for n in [x for x in notifications][0:25]:
            #print(f"{n.id} - {n.comment.id}")
            if not n.read:
                n.read=True
                db.add(n)
                db.commit()

        return render_template("notifications.html",
                               v=self,
                               notifications=comments,
                               next_exists=next_exists,
                               page=page)
    
    @property
    def notifications_count(self):

        return self.notifications.filter_by(read=False, is_banned=False, is_deleted=False).count()

    @property
    def post_count(self):

        return self.submissions.filter_by(is_banned=False).count()

    @property
    def comment_count(self):

        return self.comments.filter(text("parent_submission is not null")).filter_by(is_banned=False, is_deleted=False).count()

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

        alts1=db.query(User).join(Alt, Alt.user2==User.id).filter(Alt.user1==self.id).all()
        alts2=db.query(User).join(Alt, Alt.user1==User.id).filter(Alt.user2==self.id).all()

        output= list(set([x for x in alts1]+[y for y in alts2]))
        output=sorted(output, key=lambda x: x.username)

        return output
        

    def has_follower(self, user):

        return self.followers.filter_by(user_id=user.id).first()

    def set_profile(self, file):

        self.del_profile()
        self.profile_nonce+=1

        aws.upload_file(name=f"users/{self.username}/profile-{self.profile_nonce}.png",
                        file=file,
                        resize=(100,100)
                        )
        self.has_profile=True
        db.add(self)
        db.commit()
        
    def set_banner(self, file):

        self.del_banner()
        self.banner_nonce+=1

        aws.upload_file(name=f"users/{self.username}/banner-{self.banner_nonce}.png",
                        file=file)

        self.has_banner=True
        db.add(self)
        db.commit()

    def del_profile(self):

        aws.delete_file(name=f"users/{self.username}/profile-{self.profile_nonce}.png")
        self.has_profile=False
        db.add(self)
        db.commit()

    def del_banner(self):

        aws.delete_file(name=f"users/{self.username}/banner-{self.banner_nonce}.png")
        self.has_banner=False
        db.add(self)
        db.commit()

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

        titles=[i for i in db.query(Title).order_by(text("id asc")).all() if eval(i.qualification_expr,{}, locs)]
        return titles

    @property
    def can_make_guild(self):

        if self.karma + self.comment_karma < 50:
            return False

        if len(self.boards_modded) >= 10:
            return False

        return True
    
    @property
    def can_join_gms(self):
        return len(self.boards_modded) < 10
    

    @property
    def can_siege(self):

        if self.is_banned:
            return False

        now=int(time.time())

        return now-self.last_siege_utc > 60*60*24*30

    @property
    def json(self):

        if self.is_banned:
            return {'username':self.username,
                    'permalink':self.permalink,
                    'is_banned':True,
                    'ban_reason':self.ban_reason,
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
                'comment_count':self.comment_count
                }

    @property
    def total_karma(self):

        return  max(self.karma+self.comment_karma, -5)

    @property        
    def can_use_darkmode(self):
        return True
        #return self.referral_count or self.has_earned_darkmode or self.has_badge(16) or self.has_badge(17)


    def ban(self, admin, include_alts=True):

        #Takes care of all functions needed for account termination

        self.del_banner()
        self.del_profile()
        self.is_banned=admin.id
        db.add(self)
        db.commit()

        if include_alts:
            for alt in self.alts:
                alt.ban(admin=admin, include_alts=False)

    def unban(self):

        #Takes care of all functions needed for account reinstatement.

        self.is_banned=0

        db.add(self)
        db.commit()