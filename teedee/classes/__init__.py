from dbModels import *
from flask import Flask

app = Flask(__name__, template_folder='../templates', static_folder='../static')

@app.route("/")
def index():
    return "Hello Bros"


if __name__ == "__main__":
    app.run(host='localhost', port=5000, debug=True)