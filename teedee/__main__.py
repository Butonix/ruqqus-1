from teedee.creds.config import app
from teedee.classes.dbModels import *

@app.route("/test")
def test():
    return "Hello Bros"
