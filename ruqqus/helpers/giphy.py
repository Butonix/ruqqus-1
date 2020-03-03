from flask import *
from os import environ
import requests

from ruqqus.__main__ import app

@app.route("/giphy", methods=["GET"])
@app.route("/giphy?searchTerm=<searchTerm>", methods=["GET"])
def giphy(searchTerm=None):
    if searchTerm:
        url = f"https://api.giphy.com/v1/gifs/search?q={searchTerm}&api_key={environ.get('GIPHY_KEY')}&limit=48"
    else:
        url = f"https://api.giphy.com/v1/gifs?api_key={environ.get('GIPHY_KEY')}&limit=48"
    return requests.get(url)