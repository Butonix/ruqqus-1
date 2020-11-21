from os import environ
import requests

from flask import *

from ruqqus.classes import *
from ruqqus.helpers.wrappers import *
from ruqqus.helpers.security import *
import ruqqus.helpers.discord
from ruqqus.__main__ import app

SERVER_ID = environ.get("DISCORD_SERVER_ID",'').rstrip()
CLIENT_ID = environ.get("DISCORD_CLIENT_ID",'').rstrip()
CLIENT_SECRET = environ.get("DISCORD_CLIENT_SECRET",'').rstrip()
BOT_TOKEN = environ.get("DISCORD_BOT_TOKEN").rstrip()
DISCORD_ENDPOINT = "https://discordapp.com/api/v6"


@app.route("/discord", methods=["GET"])
def discord_server():
    return redirect("https://discord.gg/3Y5Dd4Y")


@app.route("/guilded", methods=["GET"])
def guilded_server():
    return redirect("https://www.guilded.gg/i/VEvjaraE")


@app.route("/join_discord", methods=["GET"])
@auth_required
def join_discord(v):

	state=generate_hash(f"{session.get('session_id')}+{v.id}+discord")

	return redirect(f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri=https%3A%2F%2F{app.config['SERVER_NAME']}%2Fdiscord_redirect&response_type=code&scope=identify%20guilds.join&state={state}")

@app.route("/discord_redirect", methods=["GET"])
@auth_required
def discord_redirect(v):

	state=request.args.get('state','')

	if not validate_hash(f"{session.get('session_id')}+{v.id}+discord", state):
		abort(403)

	return ('so far so good')


