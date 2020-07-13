from os import environ
import requests

from flask import *

from ruqqus.classes import *
from ruqqus.helpers.wrappers import *
from ruqqus.helpers.security import *
import ruqqus.helpers.discord
from ruqqus.__main__ import app

SERVER_ID=environ.get("DISCORD_SERVER_ID")
CLIENT_ID=environ.get("DISCORD_CLIENT_ID")
CLIENT_SECRET=environ.get("DISCORD_CLIENT_SECRET")
BOT_TOKEN=environ.get("DISCORD_BOT_TOKEN")
DISCORD_ENDPOINT="https://discordapp.com/api/v6"

@app.route("/discord", methods=["GET"])
def discord_server():
	return redirect("https://discord.gg/3Y5Dd4Y")


@app.route("/guilded", methods=["GET"])
def guilded_server():
	return redirect("https://www.guilded.gg/i/VEvjaraE")