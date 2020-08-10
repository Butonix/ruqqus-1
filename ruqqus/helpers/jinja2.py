import time
import json
from os import environ
from sqlalchemy import text

from ruqqus.classes.user import User
from .get import *
import requests
from ruqqus.__main__ import app, cache



@app.template_filter("total_users")
@cache.memoize(timeout=60)
def total_users(x):

    return db.query(User).filter_by(is_banned=0).count()


@app.template_filter("source_code")
@cache.memoize(timeout=60*60*24)
def source_code(file_name):

    return open("/app/"+file_name, mode="r+").read()

@app.template_filter("full_link")
def full_link(url):

    return f"https://{app.config['SERVER_NAME']}{url}"

@app.template_filter("env")
def env_var_filter(x):

    x=environ.get(x, 1)

    try:
        return int(x)
    except:
        try:
            return float(x)
        except:
            return x
        
@app.template_filter("js_str_escape")
def js_str_escape(s):
    
    s=s.replace("'", r"\'")

    return s

@app.template_filter("is_mod")
@cache.memoize(60)
def jinja_is_mod(uid, bid):

    return bool(get_mod(uid, bid))

@app.template_filter('goals')
@cache.memoize(3600)
def patreon_goals():

    refresh_token = environ.get('PATREON_REFRESH_TOKEN')
    client_id = environ.get("PATREON_CLIENT_ID")
    client_secret = environ.get("PATREON_CLIENT_SECRET")

    # step 1: obtain new access token
    url = "https://www.patreon.com/api/oauth2/token"
    params = {"grant_type": 'refresh_token',
              "client_id": client_id,
              "client_secret": client_secret,
              "refresh_token": refresh_token}

    x = requests.get(url, params=params)

    access_token = x.json()["access_token"]

    # step 2: obtain campaign info
    url = "https://www.patreon.com/api/oauth2/api/current_user/campaigns"
    headers = {"Authorization": "Bearer: " + access_token}

    x = requests.get(url, headers=headers)

    data = x.json()

    # get current support total
    total_support_cents = data["data"][0]["attributes"]["pledge_sum"]

    # get goal amounts - looking for lowest incomplete goal
    goal_cents = 99999999
    progress = 0
    for entry in data["included"]:

        if "completed_percentage" not in entry["attributes"]:
            continue

        if entry["attributes"]['amount_cents'] < goal_cents and entry["attributes"]["completed_percentage"] < 100:
            goal_cents = entry["attributes"]['amount_cents']
            progress = entry["attributes"]['completed_percentage']

    #print("goal cents: " + goal_cents)
    #print("percent there: " + progress)
    return {'cents': goal_cents,
            'percent': progress}