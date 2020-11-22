from os import environ
import requests
import pprint

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

#Discord IDs
BANNED_ID="700694275905814591"
MEMBER_ID="727255602648186970"
NICK_ID="730493039176450170"
VERIFY_ID="779872346219610123"
REAL_ID="779904545194508290"

WELCOME_CHANNEL="727361062470418472"



@app.route("/guilded", methods=["GET"])
def guilded_server():
    return redirect("https://www.guilded.gg/i/VEvjaraE")


@app.route("/discord", methods=["GET"])
@auth_required
def join_discord(v):

    state=generate_hash(f"{session.get('session_id')}+{v.id}+discord")

    return redirect(f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri=https%3A%2F%2F{app.config['SERVER_NAME']}%2Fdiscord_redirect&response_type=code&scope=identify%20guilds.join&state={state}")

@app.route("/discord_redirect", methods=["GET"])
@auth_required
def discord_redirect(v):


    #validate state
    state=request.args.get('state','')

    if not validate_hash(f"{session.get('session_id')}+{v.id}+discord", state):
        abort(400)

    #get discord token
    code = request.args.get("code","")
    if not code:
        abort(400)

    data={
        "client_id":CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': f"https://{app.config['SERVER_NAME']}/discord_redirect",
        'scope': 'identify guilds.join'
    }
    headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    url="https://discord.com/api/oauth2/token"

    x=requests.post(url, headers=headers, data=data)

    x=x.json()


    try:
        token=x["access_token"]
    except KeyError:
        abort(403)


    #get user ID
    url="https://discord.com/api/users/@me"
    headers={
        'Authorization': f"Bearer {token}"
    }
    x=requests.get(url, headers=headers)

    x=x.json()



    #add user to discord
    headers={
        'Authorization': f"Bot {BOT_TOKEN}",
        'Content-Type': "application/json"
    }

    #remove existing user if applicable
    if v.discord_id and v.discord_id != x['id']:
        url=f"https://discord.com/api/guilds/{SERVER_ID}/members/{v.discord_id}"
        requests.delete(url, headers=headers)

    v.discord_id=x["id"]
    g.db.add(v)
    g.db.commit()

    url=f"https://discord.com/api/guilds/{SERVER_ID}/members/{x['id']}"

    roles=[VERIFY_ID]
    name=v.username
    if v.is_banned and v.unban_utc==0:
        roles.append(BANNED_ID)
    if v.real_id:
        roles.append(REAL_ID)
        name+= f" | {v.real_id}"

    data={
        "access_token":token,
        "nick":name,
        "roles": roles
    }

    x=requests.put(url, headers=headers, json=data)

    #check on if they are already there
    #print(x.status_code)

    if x.status_code==204:

        ##if user is already a member, remove old roles and update nick
        discord_no_nick_role(v)
        discord_linked_role(v)

        if v.real_id:
            discord_real_role(v)


        url=f"https://discord.com/api/guilds/{SERVER_ID}/members/{v.discord_id}"
        data={
            "nick": name
        }

        req=requests.patch(url, headers=headers, json=data)

        #print(req.status_code)
        #print(url)

        print

    return redirect(f"https://discord.com/channels/{SERVER_ID}/{WELCOME_CHANNEL}")

def discord_ban_role(user):

    if not user.discord_id:
        return

    url=f"https://discord.com/api/guilds/{SERVER_ID}/members/{user.discord_id}/roles/{BANNED_ID}"
    headers={
        "Authorization": f"Bot {BOT_TOKEN}"
    }
    requests.put(url, headers=headers)

    url=f"https://discord.com/api/guilds/{SERVER_ID}/members/{user.discord_id}/roles/{MEMBER_ID}"
    requests.delete(url, headers=headers)


def discord_unban_role(user):

    if not user.discord_id:
        return

    url=f"https://discord.com/api/guilds/{SERVER_ID}/members/{user.discord_id}/roles/{BANNED_ID}"
    headers={
        "Authorization": f"Bot {BOT_TOKEN}"
    }
    requests.delete(url, headers=headers)

def discord_no_nick_role(user):

    if not user.discord_id:
        return

    #print("discord no nick")

    url=f"https://discord.com/api/guilds/{SERVER_ID}/members/{user.discord_id}/roles/{NICK_ID}"
    headers={
        "Authorization": f"Bot {BOT_TOKEN}"
    }
    requests.delete(url, headers=headers)

def discord_real_role(user):

    if not user.discord_id:
        return

    url=f"https://discord.com/api/guilds/{SERVER_ID}/members/{user.discord_id}/roles/{REAL_ID}"
    headers={
        "Authorization": f"Bot {BOT_TOKEN}"
    }
    requests.put(url, headers=headers)

def discord_linked_role(user):

    if not user.discord_id:
        return

    url=f"https://discord.com/api/guilds/{SERVER_ID}/members/{user.discord_id}/roles/{VERIFY_ID}"
    headers={
        "Authorization": f"Bot {BOT_TOKEN}"
    }
    requests.put(url, headers=headers)


