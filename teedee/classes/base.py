from os import environ
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

_engine=create_engine(envron.get("DATABASE_URL"))
db = sessionmaker(bind=_engine)()


Base=declarative_base()



        
