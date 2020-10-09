from ruqqus.__main__ import app, db_session
from ruqqus import classes
from ruqqus.mail import send_mail
from ruqqus.helpers.get import get_user
from flask import render_template

db=db_session()

title = input("Title: ")
subject = input("Email subject: ")

x = db.query(classes.user.User).filter(classes.user.User.is_banned==0, classes.user.User.email!=None)
print(f"total mail to send: {x.count()}")

#for user in x.order_by(classes.user.User.id.asc()).all():
for user in [get_user('captainmeta4', nSession=db)]:
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
