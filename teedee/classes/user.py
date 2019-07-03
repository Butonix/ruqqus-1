from base import *

class User(Base):

    __tablename__="users"

    id=Column(Integer, primary_key=True)
    username=Column(String)
    email=Column(String)
    passhash=Column(String)
    created_utc=Column(Integer)
    is_admin=Column(Boolean)
    is_banned=Column(Boolean)
        
