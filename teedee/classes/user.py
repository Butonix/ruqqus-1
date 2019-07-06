from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, session
from teedee.helpers.base36 import *
from teedee.__main__ import Base, db
from time import strftime, time
from sqlalchemy import *
from sqlalchemy.orm import relationship
import hmac
from os import environ
from secrets import token_hex

class User(Base):

    __tablename__="users"
    id = Column(BigInteger, primary_key=True)
    username = Column(String, default=None)
    email = Column(String, default=None)
    passhash = Column(String, default=None)
    created_utc = Column(BigInteger, default=0)
    admin_level = Column(Integer, default=0)
    is_banned = Column(Boolean, default=False)
    ips = relationship('IPs', backref='users')
    username_verified = Column(Boolean, default=False)

    def __init__(self, **kwargs):

        if "password" in kwargs:

            kwargs["passhash"]=self.hash_password(kwargs["password"])
            kwargs.pop("password")

        kwargs["created_utc"]=int(time())

        super().__init__(**kwargs)

    def hash_password(self, password):
        return generate_password_hash(password, method='pbkdf2:sha512', salt_length=8)

    def verifyPass(self, password):
        return check_password_hash(self.passhash, password)
    
    def rendered_userpage(self, v=None):

        if not self.is_banned:
            return render_template("userpage.html", u=self, v=v)
        else:
            return render_template("userpage_banned.html", u=self, v=v)

    @property
    def formkey(self):

        if "session_id" not in session:
            session["session_id"]=token_hex(16)

        return hmac.new(key=bytes(environ.get("MASTER_KEY"), "utf-16"),
                        msg=bytes(session["session_id"]+str(self.id), "utf-16")
                        ).hexdigest()

    def validate_formkey(self, formkey):

        return hmac.compare_digest(formkey, self.formkey)
    
    def verify_username(self, username):
        
        #no reassignments allowed
        if self.username_verified:
            return render_template("settings.html", v=self, error="Your account has already validated its username.")
        
        #For use when verifying username with reddit
        #Set username. Randomize username of any other existing account with same
        try:
            existing = session.query(User).filter_by(username=username).all()[0]

            #No reassignments allowed
            if existing.username_verified:
                return render_template("settings.html", v=self, error="Another account has already validated that username.")
                
            # Rename new account to user_id
            # guaranteed to be unique
            existing.username=f"user_{existing.id}"
            
            db.add(existing)
                                     
        except IndexError:
            pass
                                      
        self.username=username
        self.username_verified=True
        
        db.add(self)
        db.commit()

        return render_template("settings.html", v=self, msg="Your account name has been updated and validated.")

    @property
    def url(self):
        return f"/u/{self.username}"

    @property
    def created_date(self):

        print(self.created_utc)

        return strftime("%d %B %Y", time.gmtime(self.created_utc))

    def __repr__(self):
        return f"<User(username={self.username})>"
