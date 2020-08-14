from os import environ
import requests
import urllib
import hmac
import pprint

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

    url=f"https://www.patreon.com/oauth2/authorize?response_type=code&client_id={PATREON_CLIENT_ID}&redirect_uri={redirect_uri}&state={state}&scope=identity"

    return redirect(url)

@app.route("/patreon_unauthorize", methods=["POST"])
@auth_required
def patreon_unauthorize(v):

    v.patreon_id=None
    v.patreon_name=None
    v.patreon_refresh_token=''
    v.patreon_access_token=''
    v.patreon_pledge_cents=0
    v.patreon_name=""

    if v.title_id in [32, 33, 34, 35]:
        v.title_id=None

    v.refresh_selfset_badges()
    
    g.db.add(v)
    g.db.commit()

    return render_template("settings_profile.html",
                                   v=v,
                                   msg=f"Patreon account un-linked."
                                   )


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

    #print(data)

    v.access_token=data["access_token"]
    v.refresh_token=data["refresh_token"]

    #get membership status
    url="https://www.patreon.com/api/oauth2/v2/identity"
    params={"include":"memberships",
  		"fields[user]":"vanity,full_name",
  		"fields[member]":"currently_entitled_amount_cents"}
    headers={"Authorization":f"Bearer {v.access_token}"}

    #print(headers)

    data=requests.get(url, params=params, headers=headers).json()

    #parse response for data


    print(data)

    patreon_id = data["data"]["id"]
    existing=g.db.query(User).filter_by(patreon_id=patreon_id).first()
    if existing:
        return  render_template("settings_profile.html",
                                   v=v,
                                   error=f"That Patreon account is already linked to another Ruqqus user."
                                   )

    v.patreon_id=data["data"]["id"]
    v.patreon_name=data["data"]["attributes"]["vanity"] or data["data"]["attributes"]["full_name"] or f"ID: {data['data']['id']}"


    try:
        v.patreon_pledge_cents=data['included'][0]["attributes"]['currently_entitled_amount_cents']
    except Exception as e:
        print(e)
        v.patreon_pledge_cents=0


    g.db.add(v)
    g.db.commit()

    v.refresh_selfset_badges()
    g.db.add(v)

    g.db.commit()

    return  render_template("settings_profile.html",
                                   v=v,
                                   msg=f"Patreon account {v.patreon_name} linked successfully."
                                   )

@app.route("/webhook/patreon", methods=["POST"])
def webhook_patreon():

    
    #validate that request is from patreon
    sig = request.headers.get('X-Patreon-Signature')
    if not sig:
        abort(400)

    hash_= hmac.new(key=bytes(environ.get("PATREON_SECRET"), "utf-8"),
                    msg=request.get_data(),
                    digestmod='md5'
                    ).hexdigest()

    if not hmac.compare_digest(sig, hash_):
        abort(401)

    #look up user by patreon id

    data=request.json

    #pprint.pprint(data)

    user = g.db.query(User).filter_by(patreon_id=data["data"]["id"]).first()
    if not user:
        return "", 204

    event_type=request.headers.get("X-Patreon-Event")

    if event_type in ["members:pledge:create","members:pledge:update"]:
        user.patreon_pledge_cents=data["data"]["attributes"]["pledge_amount_cents"]
    elif event_type=="members:pledge:delete":
        user.patreon_pledge_cents=0
    else:
        abort(400)

    #print(user)

    #print(user.patreon_pledge_cents)

    g.db.add(user)
    g.db.flush()

    #Change patron title if appropriate
    if user.patreon_pledge_cents==0 and user.title_id in [32, 33, 34, 35]:
        user.title_id=None
    elif user.patreon_pledge_cents<500 and user.title_id in [33, 34, 35]:
        user.title_id=32
    elif user.patreon_pledge_cents<2000 and user.title_id in [32, 34, 35]:
        user.title_id=33
    elif user.patreon_pledge_cents<5000 and user.title_id in [32, 33, 35]:
        user.title_id=34
    elif user.patreon_pledge_cents>=5000 and user.title_id in [32, 33, 34]:
        user.title_id=35

    #print(user.title_id)

    g.db.add(user)
    g.db.flush()

    user.refresh_selfset_badges()

    g.db.commit()

    #print(user.patreon_pledge_cents)
    #print(user.title_id)

    return "", 204