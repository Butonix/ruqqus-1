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




r=redis.Redis(host=app.config["CACHE_REDIS_URL"][0:-5], decode_responses=True, ssl_cert_reqs=None)
UNDER_ATTACK=r.get("under_attack") or 0
TIMEOUT_STAMP=r.get("timeout_stamp") or 0

def site_performance(time):

    #every 100 requests update status from shared cache
    i+=1
    if not i%100:
        UNDER_ATTACK=cache.get("under_attack",False)
        TIMEOUT_STAMP=cache.get("timeout_stamp",0)

    recent_reqs.append(time)

    if not UNDER_ATTACK and len(recent_reqs)>=100:
        avg=sum(recent_reqs)/len(recent_reqs)

        if avg>3.0:

            data={"value":"under_attack"}
            x=requests.patch(url, headers=headers, json=data)

            if x.status_code<300:
                r.set("under_attack",1)
                UNDER_ATTACK=1
                ts=int(time.time())+3600
                r.set("timeout_stamp", ts)
                TIMEOUT_STAMP=ts

    elif UNDER_ATTACK:
        if time.time()>ts:
            data={"value":"high"}
            x=requests.patch(url, headers=headers, json=data)

            if x.status_code<300:
                r.set("under_attack",0)
                UNDER_ATTACK=0
                TIMEOUT_STAMP=ts


