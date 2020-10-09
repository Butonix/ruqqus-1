from os import environ
import requests
from ruqqus.__main__ import cache

SERVER_ID = environ.get("DISCORD_SERVER_ID")
CLIENT_ID = environ.get("DISCORD_CLIENT_ID")
CLIENT_SECRET = environ.get("DISCORD_CLIENT_SECRET")
DISCORD_ENDPOINT = "https://discordapp.com/api/v6"
BOT_TOKEN = environ.get("DISCORD_BOT_TOKEN")

ROLES = {"banned": 700694275905814591,
         "ruqqie": 701074500372004915
         }


def add_role(user, role_name):

    role_id = ROLES[role_name]
    url = f"/guilds/{SERVER_ID}/members/{v.discord_id}/roles/{role_id}"
    headers = {"Authorization": f"Bot {BOT_TOKEN}"}
    requests.put(url)


def delete_role(user, role_name):
    role_id = ROLES[role_name]
    url = f"/guilds/{SERVER_ID}/members/{v.discord_id}/roles/{role_id}"
    headers = {"Authorization": f"Bot {BOT_TOKEN}"}
    requests.delete(url)
