import time
from sqlalchemy import *
from sqlalchemy.orm import relationship
from flask import g, request
import random

from ruqqus.helpers.base36 import *
from .mix_ins import *
from ruqqus.__main__ import app, Base


class Image(Base):
    __tablename__ = "images"
    id = Column(BigInteger, primary_key=True)
    state = Column(String(8))
    number = Column(Integer)
    text = Column(String(64))

    @property
    def path(self):
        return f"/assets/images/states/{self.state.lower()}-{self.number}.jpg"



def random_image():
    n=g.db.query(Image).count()
    return g.db.query(Image).order_by(Image.id.asc()).offset(random.randint(0,n-1)).first()



class BadPic(Base):

    #Class for tracking fuzzy hashes of banned csam images

    __tablename__="badpics"
    id = Column(BigInteger, primary_key=True)
    description=Column(String(255), default=None)
    phash=Column(String(64))
    ban_reason=Column(String(64))
    ban_time=Column(Integer)


class GuildImage(Base, Stndrd):

    __tablename__="guild_images"
    board_id = Column(Integer, ForeignKey("boards.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_utc = Column(Integer)
    creation_ip = Column(String(128)),
    creation_region = Column(String(2))
    name=Column(String(64))

    user = relationship("User")
    board = relationship("Board")

    def __init__(self, **kwargs):

        kwargs['created_utc'] = int(time.time())
        kwargs['creation_ip'] = request.remote_addr
        kwargs['creation_region'] = request.headers("cf-ipcountry")

        super().__init__(**kwargs)


    @property
    def S3_name(self):
        return f"board/{self.board.name.lower()}/css/{self.base36id}"
    

    @property
    def permalink(self):

        return f"https://{app.config["S3_BUCKET"]}/{self.S3_name}"