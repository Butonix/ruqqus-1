from ruqqus.__main__ import app, db
from ruqqus import classes
from ruqqus.mail import send_mail
from flask import render_template

title = input("Title: ")
subject = input("Email subject: ")


with app.app_context():
    html=render_template(
        "email/mailing.html",
        title=title,
        preheader=content[0:100],
        content=content
        )

#for user in db.query(classes.user.User).filter_by(is_activated=True, is_banned=0, is_deleted=False):
for user in db.query(classes.user.User).filter_by(id=7).all():

    send_mail(
        to_address=user.email,
        subject=subject,
        html=html,
        plaintext=content)

    
