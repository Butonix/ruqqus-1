from teedee.helpers.base36 import *
from teedee.__main__ import Base, db
from time import strftime
from sqlalchemy import *
from sqlalchemy.orm import relationship

    
class IP(Base):
    __tablename__ = "ips"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ip = Column(VARCHAR(40), default=None)

    def __repr__(self):
        return f"<Ips(id={self.id}, uid={self.user_id}, ip={self.ip})>"
