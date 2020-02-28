from sqlalchemy import *
from ruqqus.__main__ import Base, db, cache
from .mix_ins import *

class Tag(Base, Stndrd):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey("boards.id"), default=0)
    post_id = Column(Integer, ForeignKey("submissions.id"), default=0)
    name = Column(Sring, default="")
    description = Column(String, default="")
    created_utc = Column(Integer)

    def __repr__(self):
        return f"<Tag(id={self.id})>"