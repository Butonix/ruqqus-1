from teedee.classes.dbModels import *
from os import environ
from flask import *

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get("DATABASE_URL")

@app.route("/test")
def test():
    return "Hello Bros"
