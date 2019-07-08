from os import environ
import requests

from teedee.__main__ import app

app.config['MAILGUN_KEY'] = environ.get("MAILGUN_KEY")
app.config['MAILGUN_DOMAIN'] = environ.get("MAILGUN_DOMAIN")

def send_mail(to_address, from_address, subject, plaintext, html):

    r = requests.\
        post("https://api.mailgun.net/v2/%s/messages" % app.config['MAILGUN_DOMAIN'],
            auth=("api", app.config['MAILGUN_KEY']),
             data={
                 "from": from_address,
                 "to": to_address,
                 "subject": subject,
                 "text": plaintext,
                 "html": html
             }
         )
    return r
