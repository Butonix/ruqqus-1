from os import environ
import requests

SERVER_ID = environ.get("DISCORD_SERVER_ID",'').rstrip()
CLIENT_ID = environ.get("DISCORD_CLIENT_ID",'').rstrip()
CLIENT_SECRET = environ.get("DISCORD_CLIENT_SECRET",'').rstrip()
DISCORD_ENDPOINT = "https://discordapp.com/api"
BOT_TOKEN = environ.get("DISCORD_BOT_TOKEN",'').rstrip()


ROLES={
    "banned":  "700694275905814591",
    "member":  "727255602648186970",
    "nick":    "730493039176450170",
    "linked":  "779872346219610123",
    "realid":  "779904545194508290",
    "premium": "780084870176702484",
    }

def discord_wrap(f):

    def wrapper(*args, **kwargs):

        user=args[0]
        if not user.discord_id:
            return

        return f(*args, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper



@discord_wrap
def add_role(user, role_name):

    print(BOT_TOKEN)

    role_id = ROLES[role_name]
    url = f"{DISCORD_ENDPOINT}/guilds/{SERVER_ID}/members/{user.discord_id}/roles/{role_id}"
    headers = {"Authorization": f"Bot {BOT_TOKEN}"}
    #print(url)
    x=requests.put(url)
    #print(x.status_code)
    return True

@discord_wrap
def delete_role(user, role_name):
    role_id = ROLES[role_name]
    url = f"{DISCORD_ENDPOINT}/guilds/{SERVER_ID}/members/{user.discord_id}/roles/{role_id}"
    headers = {"Authorization": f"Bot {BOT_TOKEN}"}
    #print(url)
    x=requests.delete(url)
    #print(x.status_code)
    return True
