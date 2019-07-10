from os import environ
import requests
from time import time

from teedee.__main__ import app
from teedee.helpers.security import *

app.config['MAILGUN_KEY'] = environ.get("MAILGUN_KEY")
app.config['MAILGUN_DOMAIN'] = environ.get("MAILGUN_DOMAIN")

def send_mail(to_address, subject, plaintext, html, from_address="noreply@ruqq.us"):

    url=f"https://api.mailgun.net/v2/{app.config['MAILGUN_DOMAIN']}/messages"

    payload={"from":from_address,
             "to": to_address,
             "subject":subject,
             "text":None,
             "html":html}
    

    r = requests.post("url",
                      auth=("api", app.config['MAILGUN_KEY']),
                      body=payload
                      )
    return r

def send_verification_email(user):

    url=f"https://{app.config['DOMAIN']}/api/verify_email"

    now=time()

    token=generate_hash(f"{user.email}+{user.id}+{now}")
    params=f"?time={now}&token={token}"

    link=url+params

    html="""
         <p>Thank you for signing up.
         <a href="{link}">Click here</a> to verify your email address</p>
         """

    text=f"Thank you for signing up. Click to verify your email address: {link}"

    send_mail(to_address=user.email,
              html=html,
              text=text,
              subject="Validate your Ruqqus account"
              )

