from teedee.creds.config import app
from teedee.classes.dbModels import *




@app.route("/test")
def test():
    return "Hello Bros"


if __name__ == "__main__":
    app.run(host='localhost', port=5000, debug=True)