from teedee.classes.dbModels import *
from os import environ
from flask import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import *

app = Flask(__name__,
            template_folder='./templates',
            static_folder='./static'
           )
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get("DATABASE_URL")
app.config['SECRET_KEY']=environ.get('Flask_secret_key')
app.config["SERVER_NAME"]="tee-dee.herokuapp.com"

#setup dbb
_engine = create_engine(environ.get("DATABASE_URL"))
db = sessionmaker(bind=_engine)()
Base = declarative_base()

#import and bind all routing functions
from teedee.helpers import *
from teedee.routes import *


