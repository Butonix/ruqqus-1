from collections import deque
import requests
import time
import redis
from os import environ
from ruqqus.__main__ import app

CF_KEY = environ.get("CLOUDFLARE_KEY").lstrip().rstrip()
CF_ZONE = environ.get("CLOUDFLARE_ZONE")
recent_reqs=deque([],200)



headers = {
    "Authorization": f"Bearer {CF_KEY}",
    "Content-Type": "application/json"
    }

url=f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE}/settings/security_level"




r=redis.Redis(host=app.config["CACHE_REDIS_URL"][8:], decode_responses=True, ssl_cert_reqs=None)

config={}
config['UNDER_ATTACK']=r.get("under_attack") or 0
config['TIMEOUT_STAMP']=r.get("timeout_stamp") or 0

print(f"Under attack: {config['UNDER_ATTACK']}")

config['COUNTER']=0

def site_performance(time):

    config['COUNTER']+=1

    #every 100 requests update status from shared cache
    if not config['COUNTER']%100:
        UNDER_ATTACK=r.get("under_attack") or 0
        TIMEOUT_STAMP=r.get("timeout_stamp") or 0

    recent_reqs.append(time)

    if not config['UNDER_ATTACK'] and len(recent_reqs)>=100:
        avg=sum(recent_reqs)/len(recent_reqs)

        if avg>=1.0:

            try:
                print("turning on UA mode")
            except:
                pass

            data={"value":"under_attack"}
            x=requests.patch(url, headers=headers, json=data)

            if x.status_code<300:
                r.set("under_attack",1)
                config['UNDER_ATTACK']=1
                ts=int(time.time())+3600
                r.set("timeout_stamp", ts)
                config['TIMEOUT_STAMP']=ts

    elif config['UNDER_ATTACK']:
        if time.time()>config['TIMEOUT_STAMP']:

            try:
                print("turning off UA mode")
            except:
                pass

            data={"value":"high"}
            x=requests.patch(url, headers=headers, json=data)

            if x.status_code<300:
                r.set("under_attack",0)
                config['UNDER_ATTACK']=0
                config['TIMEOUT_STAMP']=ts


