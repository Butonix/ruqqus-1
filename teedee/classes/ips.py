from teedee.helpers.base36 import *
from teedee.__main__ import Base, db
from time import strftime
from sqlalchemy import *
from .user import User

    
class IP(Base):
    __tablename__ = "Ips"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey(User.id), default=0)
    ip = Column(VARCHAR(40), default=None)

    def __repr__(self):
        return f"<Ips(id={self.id}, uid={self.user_id}, ip={self.ip})>"
