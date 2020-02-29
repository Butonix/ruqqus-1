from sqlalchemy import *
from ruqqus.__main__ import Base, db, cache
from .mix_ins import *

class Flair(Base, Stndrd):
    __tablename__ = "flairs"
    id = Column(Integer, primary_key=True)
    board_id = Column(Integer, ForeignKey("boards.id"), default=0)
    name = Column(String, default="")
    icon = Column(String(64))
    description = Column(String, default="")
    created_utc = Column(Integer)

    def __repr__(self):
        return f"<Flair(id={self.id})>"