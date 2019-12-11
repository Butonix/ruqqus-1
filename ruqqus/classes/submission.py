from flask import render_template, request, abort
import time
from sqlalchemy import *
from sqlalchemy.orm import relationship
import math
from urllib.parse import urlparse
import random

from ruqqus.helpers.base36 import *
from ruqqus.helpers.lazy import lazy
from ruqqus.__main__ import Base, db, cache
from .user import User
from .votes import Vote
from .domains import Domain
from .flags import Flag

class Submission(Base):

    __tablename__="submissions"

    id = Column(BigInteger, primary_key=True)
    author_id = Column(BigInteger, ForeignKey(User.id))
    title = Column(String(500), default=None)
    url = Column(String(500), default=None)
    edited_utc = Column(BigInteger, default=0)
    created_utc = Column(BigInteger, default=0)
    is_banned = Column(Boolean, default=False)
    is_deleted=Column(Boolean, default=False)
    distinguish_level=Column(Integer, default=0)
    created_str=Column(String(255), default=None)
    stickied=Column(Boolean, default=False)
    comments=relationship("Comment", lazy="dynamic", backref="submissions")
    body=Column(String(2000), default="")
    body_html=Column(String(2200), default="")
    embed_url=Column(String(256), default="")
    domain_ref=Column(Integer, ForeignKey("domains.id"))
    flags=relationship("Flag", lazy="dynamic", backref="submission")
    is_approved=Column(Integer, default=0)
    approved_utc=Column(Integer, default=0)


    #These are virtual properties handled as postgres functions server-side
    #There is no difference to SQLAlchemy, but they cannot be written to
    #appts = db.session.query(Appointment).from_statement(func.getopenappointments(current_user.id))
    ups = Column(Integer, server_default=FetchedValue())
    downs=Column(Integer, server_default=FetchedValue())
    age=Column(Integer, server_default=FetchedValue())
    comment_count=Column(Integer, server_default=FetchedValue())
    flag_count=Column(Integer, server_default=FetchedValue())
    score=Column(Float, server_default=FetchedValue())
    rank_hot=Column(Float, server_default=FetchedValue())
    rank_fiery=Column(Float, server_default=FetchedValue())
    

    def __init__(self, *args, **kwargs):

        if "created_utc" not in kwargs:
            kwargs["created_utc"]=int(time.time())
            kwargs["created_str"]=time.strftime("%I:%M %p on %d %b %Y", time.gmtime(kwargs["created_utc"]))


        super().__init__(*args, **kwargs)
        
    def __repr__(self):
        return f"<Submission(id={self.id})>"


    @property
    #@cache.memoize(timeout=60)
    def domain_obj(self):
        if not self.domain_ref:
            return None
        
        return db.query(Domain).filter_by(id=self.domain_ref).first()


    @property
    @cache.memoize(timeout=60)
    def score_percent(self):
        try:
            return int((self.ups/(self.ups+self.downs))*100)
        except ZeroDivisionError:
            return 0

    @property
    def base36id(self):
        return base36encode(self.id)

    @property
    def fullname(self):
        return f"t2_{self.base36id}"

    @property
    def permalink(self):
        return f"/post/{self.base36id}"
                                      
    def rendered_page(self, comment=None, v=None):

        #check for banned
        if self.is_banned:
            if v and v.admin_level>=3:
                template="submission.html"
            else:
                template="submission_banned.html"
        else:
            template="submission.html"

        #load and tree comments
        #calling this function with a comment object will do a comment permalink thing
        self.tree_comments(comment=comment)
        
        #return template
        return render_template(template, v=v, p=self, sort_method=request.args.get("sort","Hot").capitalize(), linked_comment=comment)

    @property
    @lazy
    def author(self):
        return db.query(User).filter_by(id=self.author_id).first()


    @property
    @lazy
    def domain(self):

        if not self.url:
            return "text post"
        domain= urlparse(self.url).netloc
        if domain.startswith("www."):
            domain=domain.split("www.")[1]
        return domain
    
    @property
    def score_fuzzed(self, k=0.01):
        real=self.score
        a=math.floor(real*(1-k))
        b=math.ceil(real*(1+k))
        return random.randint(a,b)        

    def tree_comments(self, comment=None):

        def tree_replies(thing, layer=1):

            thing.__dict__["replies"]=[]
            i=len(comments)-1
        
            while i>=0:
                if comments[i].parent_fullname==thing.fullname:
                    thing.__dict__["replies"].append(comments[i])
                    comments.pop(i)

                i-=1
                
            if layer <=8:
                for reply in thing.replies:
                    tree_replies(reply, layer=layer+1)
                
        ######
                
        if comment:
            self.replies=[comment]
            return



        #get sort type
        sort_type = request.args.get("sort","hot")


        #Treeing is done from the end because reasons, so these sort orders are reversed
        if sort_type=="hot":
            comments=self.comments.order_by(text("comments.rank_hot ASC")).all()
        elif sort_type=="top":
            comments=self.comments.order_by(text("comments.score ASC")).all()
        elif sort_type=="new":
            comments=self.comments.order_by(text("comments.created_utc")).all()
        elif sort_type=="disputed":
            comments=self.comments.order_by(text("comments.rank_fiery ASC")).all()
        elif sort_type=="random":
            c=self.comments.all()
            comments=random.sample(c, k=len(c))
        else:
            abort(422)



        tree_replies(self)

        

        
    @property
    def age_string(self):

        age=self.age

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
            years=now.tm_year-ctd.tm_year
            return f"{years} year{'s' if years>1 else ''} ago"

    @property
    def edited_string(self):

        age=int(time.time())-self.edited_utc

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
            years=now.tm_year-ctd.tm_year
            return f"{years} year{'s' if years>1 else ''} ago"
        

    @property
    def created_date(self):
        return time.strftime("%d %B %Y", time.gmtime(self.created_utc))

    @property
    def edited_date(self):
        return time.strftime("%d %B %Y", time.gmtime(self.edited_utc))

    @property
    def active_flags(self):
        if self.is_approved:
            return 0
        else:
            return self.flags.filter(Flag.created_utc>self.approved_utc).count()

    @property
    def approved_by(self):
        return db.query(User).filter_by(id=self.is_approved).first()
