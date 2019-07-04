from teedee.creds.config import app
from teedee.classes.dbModels import *
from os import environ

@app.route("/test")
def test():
    return "Hello Bros"
