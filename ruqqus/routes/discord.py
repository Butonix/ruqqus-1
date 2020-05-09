from os import environ
import requests

from flask import *

from ruqqus.classes import *
from ruqqus.helpers.wrappers import *
from ruqqus.helpers.security import *
import ruqqus.helpers.discord
from ruqqus.__main__ import app, db

SERVER_ID=environ.get("DISCORD_SERVER_ID")
CLIENT_ID=environ.get("DISCORD_CLIENT_ID")
CLIENT_SECRET=environ.get("DISCORD_CLIENT_SECRET")
BOT_TOKEN=environ.get("DISCORD_BOT_TOKEN")
DISCORD_ENDPOINT="https://discordapp.com/api/v6"

@app.route("/discord_redirect", methods=["GET"])
@auth_required
def discord_redirect(v):

	#verify state
	s=f"{session['session_id']}+{v.login_nonce}+{v.id}"

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
	    'grant_type': 'authorization_code',
	    'code': code,
	    'redirect_uri': f"https://{app.config['SERVER_NAME']}{request.path}",
	    'scope': 'identify guilds.join'
	}
	headers={"Content-Type":"application/x-wwww-form-urlencoded"}

	print(url)
	print(data)
	print(headers)

	x=requests.post(url, json=data, headers=headers, auth=(CLIENT_ID, CLIENT_SECRET))

	#extract auth token from response
	data=x.json()
	print(data)

	token=data["access_token"]

	#remove existing discord account
	if v.discord_id:
		url=f"{DISCORD_ENDPOINT}/guilds/{SERVER_ID}/members/{v.discord_id}"
		headers={"Authorization":f"Bot {BOT_TOKEN}"}
		requests.delete(url, headers=headers)

	#get identity of discord account
	url=f"{DISCORD_ENDPOINT}/users/@me"
	headers = {"Authorization":f"Bearer {token}"}
	x=requests.get(url, headers=headers)
	data=x.json()
	discord_id=data["id"]
	v.discord_id=discord_id

	db.add(v)
	db.commit()

	#add user to discord
	url=f"{DISCORD_ENDPOINT}/guilds/{SERVER_ID}/members/{discord_id}"
	x=requests.put(url, headers=headers)

	if v.is_banned:
		discord.add_role(v, "banned")
	else:
		discord.add_role(v, "ruqqie")

	return redirect(f"https://discordapp.com/channels/{SERVER_ID}/599258778520518678")



@app.route("/discord_verify", methods=["GET"])
@auth_required
def discord(v):

	s=f"{session['session_id']}+{v.login_nonce}+{v.id}"

	state=generate_hash(s)

	session["state"]=state

	url=f"https://discordapp.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri=https%3A%2F%2Fruqqus.com%2Fdiscord_redirect&response_type=code&scope=identify%20guilds.join&state={state}"

	return redirect(url)	

@app.route("/discord", methods=["GET"])
def discord_server():
	return redirect("https://discord.gg/vzEhjFb")