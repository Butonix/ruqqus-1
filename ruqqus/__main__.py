from os import environ
from flask import *
from flaskext.markdown import Markdown
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import *

_version = "0.3.5.3"

app = Flask(__name__,
            template_folder='./templates',
            static_folder='./static'
           )
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get("DATABASE_URL")
app.config['SECRET_KEY']=environ.get('MASTER_KEY')
app.config["SERVER_NAME"]=environ.get("domain", None)
app.config["VERSION"]="0.1.0"

Markdown(app)

#setup db
_engine = create_engine(environ.get("DATABASE_URL"))
db = sessionmaker(bind=_engine)()
Base = declarative_base()

#import and bind all routing functions
from ruqqus.classes import *
from ruqqus.routes import *
import ruqqus.helpers.jinja2
import ruqqus.helpers.db_prep

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', "Origin, X-Requested-With, Content-Type, Accept, x-auth"
                         )
    return response
    
