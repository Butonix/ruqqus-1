from teedee.classes.dbModels import *
from os import environ
from flask import *
from teedee.helpers import *

app = Flask(__name__,
            template_folder='./templates',
            static_folder='./static'
           )
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get("DATABASE_URL")
app.config['SECRET_KEY']=environ.get('Flask_secret_key')
app.config["SERVER_NAME"]="tee-dee.herokuapp.com"

#import and bind all routing functions
from teedee.routes import *


