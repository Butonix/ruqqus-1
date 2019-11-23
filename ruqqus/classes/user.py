from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, session, request
from time import strftime, time, gmtime
from sqlalchemy import *
from sqlalchemy.orm import relationship, deferred
from os import environ
from secrets import token_hex
import random

from ruqqus.helpers.base36 import *
from ruqqus.helpers.security import *
from ruqqus.helpers.lazy import lazy
from .votes import Vote
from .alts import Alt
from ruqqus.__main__ import Base, db, cache

class User(Base):

    __tablename__="users"
    id = Column(Integer, primary_key=True)
    username = Column(String, default=None)
    email = Column(String, default=None)
    passhash = Column(String, default=None)
    created_utc = Column(BigInteger, default=0)
    admin_level = Column(Integer, default=0)
    is_activated = Column(Boolean, default=False)
    reddit_username = Column(String, default=None)
    over_18=Column(Boolean, default=False)
    creation_ip=Column(String, default=None)
    most_recent_ip=Column(String, default=None)
    submissions=relationship("Submission", lazy="dynamic", backref="users")
    comments=relationship("Comment", lazy="dynamic", primaryjoin="Comment.author_id==User.id")
    votes=relationship("Vote", lazy="dynamic", backref="users")
    commentvotes=relationship("CommentVote", lazy="dynamic", backref="users")
    bio=deferred(Column(String, default=""))
    bio_html=deferred(Column(String, default=""))
    badges=relationship("Badge", lazy="dynamic", backref="user")
    real_id=Column(String, default=None)
    notifications=relationship("Notification", lazy="dynamic", backref="user")
    referred_by=Column(Integer, default=None)
    is_banned=Column(Integer, default=0)
    ban_reason=Column(String, default="")

    #properties defined as SQL server-side functions
    energy = deferred(Column(Integer, server_default=FetchedValue()))
    referral_count=deferred(Column(Integer, server_default=FetchedValue()))

    def __init__(self, **kwargs):

        if "password" in kwargs:

            kwargs["passhash"]=self.hash_password(kwargs["password"])
            kwargs.pop("password")

        kwargs["created_utc"]=int(time())

        super().__init__(**kwargs)

    @property
    @cache.memoize(timeout=60)
    def karma(self):
        return self.energy


    @property
    def base36id(self):
        return base36encode(self.id)

    @property
    def fullname(self):
        return f"t1_{self.base36id}"

    @property
    def banned_by(self):

        if not self.is_banned:
            return None

        return db.query(User).filter_by(id=self.is_banned).first()
    
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
    
    def update_ip(self, remote_addr):
        
        if not remote_addr==self.most_recent_ip:
            self.most_recent_ip = remote_addr
            db.add(self)

        existing=self.ips.filter_by(ip=remote_addr).first()

        if existing:
            existing.created_utc=time()
            db.add(existing)
            
        else:
            db.add(IP(user_id=self.id, ip=remote_addr))
        
        db.commit()

    def hash_password(self, password):
        return generate_password_hash(password, method='pbkdf2:sha512', salt_length=8)

    def verifyPass(self, password):
        return check_password_hash(self.passhash, password)
        
    def rendered_userpage(self, v=None):

        if self.is_banned and (not v or v.admin_level < 3):
            return render_template("userpage_banned.html", u=self, v=v)

        page=int(request.args.get("page","1"))
        page=max(page, 1)

        
        if v:
            if v.admin_level or v.id==self.id:
                listing=[p for p in self.submissions.order_by(text("created_utc desc")).offset(25*(page-1)).limit(26)]
            else:
                listing=[p for p in self.submissions.filter_by(is_banned=False).order_by(text("created_utc desc")).offset(25*(page-1)).limit(26)]
        else:
            listing=[p for p in self.submissions.filter_by(is_banned=False).order_by(text("created_utc desc")).offset(25*(page-1)).limit(26)]

        #we got 26 items just to see if a next page exists
        next_exists=(len(listing)==26)
        listing=listing[0:25]

        return render_template("userpage.html", u=self, v=v, listing=listing, page=page, next_exists=next_exists)

    def rendered_comments_page(self, v=None):

        if self.is_banned and (not v or v.admin_level < 3):
            return render_template("userpage_banned.html", u=self, v=v)
        
        page=int(request.args.get("page","1"))

        if v:
            if v.admin_level or v.id==self.id:
                listing=[p for p in self.comments.order_by(text("created_utc desc")).offset(25*(page-1)).limit(26)]
            else:
                listing=[p for p in self.comments.filter_by(is_banned=False).order_by(text("created_utc desc")).offset(25*(page-1)).limit(26)]
        else:
            listing=[p for p in self.comments.filter_by(is_banned=False).order_by(text("created_utc desc")).offset(25*(page-1)).limit(26)]

        #we got 26 items just to see if a next page exists
        next_exists=(len(listing)==26)
        listing=listing[0:25]
        
        return render_template("userpage_comments.html", u=self, v=v, listing=listing, page=page, next_exists=next_exists)

    @property
    def formkey(self):

        if "session_id" not in session:
            session["session_id"]=token_hex(16)

        msg=f"{session['session_id']}{self.id}"

        return generate_hash(msg)

    def validate_formkey(self, formkey):

        return validate_hash(f"{session['session_id']}{self.id}", formkey)
    
    @property
    def url(self):
        return f"/u/{self.username}"

    @property
    def permalink(self):
        return self.url

    @property
    @lazy
    def created_date(self):

        return strftime("%d %B %Y", gmtime(self.created_utc))

    def __repr__(self):
        return f"<User(username={self.username})>"


    @property
    @lazy
    def color(self):

        random.seed(f"{self.id}+{self.username}")

        R=random.randint(32, 223)
        G=random.randint(32, 223)
        B=random.randint(32, 223)
        

        return str(base_encode(R, 16))+str(base_encode(G, 16))+str(base_encode(B, 16))

    def notifications_page(self, page=1, include_read=False):

        page=int(page)

        notifications=self.notifications.filter_by(is_banned=False, is_deleted=False)

        if not include_read:
            notifications=notifications.filter_by(read=False)

        notifications = notifications.order_by(text("notifications.created_utc desc")).offset(25*(page-1)).limit(25)

        comments=[n.comment for n in notifications]

        for n in notifications:
            if not n.read:
                n.read=True
                db.add(n)
                db.commit()

        return render_template("notifications.html", v=self, notifications=comments)
    
    @property
    def notifications_count(self):

        return self.notifications.filter_by(read=False, is_banned=False, is_deleted=False).count()

    @property
    @cache.memoize(timeout=60)
    def post_count(self):

        return self.submissions.filter_by(is_banned=False).count()

    @property
    @cache.memoize(timeout=60) 
    def comment_count(self):

        return self.comments.filter_by(is_banned=False, is_deleted=False).count()

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

        return list(set([x for x in alts1]+[y for y in alts2]))
        
        
