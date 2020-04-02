import imagehash
from ruqqus.__main__ import db, base

class BadPic(Base):

    __tablename__="badpics"

    id=Column(Integer, primary_key=True)
    description=Column(String(255))
    ahash=Column(String(255))
    phash=Column(String(255))
    dhash=Column(String(255))
    whash=Column(String(255))
    added_utc=Column(Integer)

    def __init__(self, image, **kwargs):

        kwargs['ahash']=imagehash.average_hash(image)
        kwargs['phash']=magehash.phash(image)
        kwargs['dhash']=magehash.dhash(image)
        kwargs['whash']=magehash.whash(image)
    
        super().__init__(**kwargs)
