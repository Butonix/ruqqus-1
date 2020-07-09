from os import environ
import requests
import urllib

from flask import *

from ruqqus.classes import *
from ruqqus.helpers.wrappers import *
from ruqqus.helpers.security import *
import ruqqus.helpers.discord
from ruqqus.__main__ import app

PATREON_SECRET=environ.get("PATREON_SECRET")

PATREON_CLIENT_ID=environ.get("PATREON_CLIENT_ID")
PATREON_CLIENT_SECRET=environ.get("PATREON_CLIENT_SECRET")

@app.route("/patreon_authorize", methods=["GET"])
@auth_required
def patreon_authorize(v):

	redirect_uri=urllib.parse.quote(f"https://{app.config['SERVER_NAME']}/redirect/patreon", safe='')

	state=generate_hash(f"{session.get('session_id')}+{v.id}")

	url=f"https://www.patreon.com/oauth2/authorize?response_type=code&client_id={PATREON_CLIENT_ID}&redirect_uri={redirect_uri}&state={state}"

	return redirect(url)


@app.route("/redirect/patreon", methods=["GET"])
@auth_required
def patreon_redirect(v):

	state=request.args.get("state", "")

	if not validate_hash(f"{session.get('session_id')}+{v.id}", state):
		abort(401)

	code=request.args.get('code','')
	if not code:
		abort(400)


	#assemble code validation
	url="https://www.patreon.com/api/oauth2/token"
	data={
		'code':code,
		'grant_type':'authorization_code',
		'client_id':PATREON_CLIENT_ID,
		'client_secret':PATREON_CLIENT_SECRET,
		'redirect_uri':f"https://{app.config['SERVER_NAME']}/redirect/patreon"
	}
	headers={
		'Content-Type':'application/x-www-form-urlencoded'
	}

	#exchange code for tokens
	x=requests.post(url, data=data, headers=headers)

	data=x.json()

	print(data)

	v.access_token=data["access_token"]
	v.refresh_token=data["refresh_token"]

	#get membership status
	url="https://www.patreon.com/api/oauth2/v2/identity"
	params={"include":"memberships"}
	headers={"Authorization":f"Bearer {v.access_token}"}

	data=requests.get(url, params=params, headers=headers).json()

	#parse response for data


	v.patreon_id=data["data"]["id"]

	print(data)

#	db.add(v)
#	db.flush()

	return '', 204



