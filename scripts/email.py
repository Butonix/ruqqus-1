from flask import render_template
import requests
from ruqqus.__main__ import db
from ruqqus.mail import send_mail

title = input("Title: ")
subject = input("Email subject: ")
preheader= input("preheader text")

content=input("content:")

html=render_template("email/mailing.html",
	title=title,
	preheader=preheader,
	content=content
	)

#for user in db.query(User).filter_by(is_activated=True, is_banned=0, is_deleted=False):
for user in db.query(User).filter_by(id=7).all():

	send_mail(
		to_address=user.email,
		subject=subject,
		html=html,
		plaintext=content)

    
