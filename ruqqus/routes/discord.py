from os import environ
import requests

from flask import *

from ruqqus.classes import *
from ruqqus.helpers.wrappers import *
from ruqqus.helpers.security import *
from ruqqus.__main__ import app, db

SERVER_ID=environ.get("DISCORD_SERVER_ID")
CLIENT_ID=environ.get("DISCORD_CLIENT_ID")
CLIENT_SECRET=environ.get("DISCORD_CLIENT_SECRET")
DISCORD_ENDPOINT="https://discordapp.com/api/v6"

@app.route("/discord_redirect", methods=["GET"])
@auth_required
def discord_redirect(v):

	#verify state
	s=f"{session['id']}+{v.login_nonce}+{v.id}"

	url_state=request.args.get("state")
	if url_state != session.get("state"):
		abort(403)

	if not validate_hash(s, url_state):
		abort(403)
	code=request.args.get("code")
	if not code:
		abort(400)

	#now exchange code for token
	url=f"{DISCORD_ENDPOINT}/oauth2/token"

	data = {
	    'client_id': CLIENT_ID,
	    'client_secret': CLIENT_SECRET,
	    'grant_type': 'authorization_code',
	    'code': code,
	    'redirect_uri': REDIRECT_URI,
	    'scope': 'identify'
	}

	x=requests.post(url)


@app.route("/discord_verify", methods=["GET"])
@auth_required
def discord_verify(v):

	s=f"{session['id']}+{v.login_nonce}+{v.id}"

	state=generate_hash(s)

	session["state"]=state

	url=f"https://discordapp.com/api/oauth2/authorize?client_id={SERVER_ID}&redirect_uri=https%3A%2F%2Fruqqus.com%2Fdiscord_redirect&response_type=code&scope=identify&state={state}"

	return redirect(url)	