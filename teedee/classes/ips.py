import time
from sqlalchemy import *
from sqlalchemy.orm import relationship

from teedee.helpers.base36 import *
from teedee.__main__ import Base, db

class IP(Base):
    __tablename__ = "ips"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ip = Column(VARCHAR(40), default=None)
    created_utc=Column(Integer, default=None)
    
    def __init__(self, *args, **kwargs):
        
        if "created_utc" not in kwargs:
            kwargs["created_utc"]=int(time.time())
        
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<Ips(id={self.id}, uid={self.user_id}, ip={self.ip})>"

    
