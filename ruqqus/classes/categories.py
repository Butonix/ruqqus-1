from ruqqus.helpers.base36 import *
from ruqqus.helpers.security import *
from sqlalchemy import *
from sqlalchemy.orm import relationship
from ruqqus.__main__ import Base, cache
from .mix_ins import *
import time


class Category(Base, Stndrd, Age_times):
    __tablename__ = "categories"
    id = Column(BigInteger, primary_key=True)
    name = Column(String(20), default="")
    description = Column(String(250), default="")
    icon = Column(String(256), default="")
    color = Column(String(128), default="")
    visible = Column(Boolean, default=True)
    created_utc = Column(Integer, default=0)

    subcats = relationship("SubCategory", lazy="joined", primaryjoin="SubCategory.cat_id==Category.id")

    def __init__(self, *args, **kwargs):
        if "created_utc" not in kwargs:
            kwargs["created_utc"] = int(time.time())

    @property
    def json(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "visible": self.visible,
            "created_date": self.created_date
        }


class SubCategory(Base, Stndrd, Age_times):
    __tablename__ = "subcategories"
    id = Column(BigInteger, primary_key=True)
    cat_id = Column(Integer, ForeignKey("categories.id"), default=0)
    name = Column(String(20), default="")
    description = Column(String(250), default="")
    created_utc = Column(Integer, default=0)

    category = relationship("Category", lazy="joined")

    def __init__(self, *args, **kwargs):
        if "created_utc" not in kwargs:
            kwargs["created_utc"] = int(time.time())

    @property
    def json(self):
        return {
            "id": self.id,
            "board_id": self.board_id,
            "cat_id": self.cat_id,
            "name": self.name,
            "description": self.description,
            "created_date": self.created_date
        }

class GuildCategory(Base, Stndrd, Age_times):
    __tablename__ = "guildcategories"
    id = Column(BigInteger, primary_key=True)
    subcat_id = Column(Integer, ForeignKey("subcategories.id"), default=0)
    board_id = Column(Integer, ForeignKey("boards.id"), default=0)
    created_utc = Column(integer, default=0)

    subcat = relationship("SubCategory", lazy="joined")
    board = relationship("Board", lazy="joined")

    def __init__(self, *args, **kwargs):
        if "created_utc" not in kwargs:
            kwargs["created_utc"] = int(time.time())
