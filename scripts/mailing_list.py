from ruqqus.__main__ import app, db
from ruqqus import classes
from ruqqus.mail import send_mail
from ruqqus.helpers.get import get_user
from flask import render_template

title = input("Title: ")
subject = input("Email subject: ")

x = db.query(classes.user.User).filter_by(is_activated=True, is_banned=0)
print(f"total mail to send: {x.count()}")

#for user in x.order_by(classes.user.User.id.asc()).all():
for user in [get_user('captainmeta4')]
    # for user in db.query(classes.user.User).filter_by(id=7).all():

    try:
        with app.app_context():
            html = render_template(
                "email/mailing.html",
                title=title,
                user=user
            )

        send_mail(
            to_address=user.email,
            subject=subject,
            html=html
        )
        print(f"[{user.id}] @{user.username}")
    except BaseException:
        print(f"unable - [{user.id}] @{user.username}")

print("all done")
