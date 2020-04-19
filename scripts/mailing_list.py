import gevent.monkey
gevent.monkey.patch_all()
print('patched')

import requests
import jinja2
from ruqqus.__main__ import db
from ruqqus import classes
from ruqqus.mail import send_mail



def render_jinja_html(template_loc,file_name,**context):

    return jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_loc+'/')
            ).get_template(file_name).render(context)

title = input("Title: ")
subject = input("Email subject: ")
preheader= input("preheader text")

content=input("content:")

html=render_jinja_html("email/mailing.html",
	title=title,
	preheader=preheader,
	content=content
	)

#for user in db.query(classes.user.User).filter_by(is_activated=True, is_banned=0, is_deleted=False):
for user in db.query(classes.user.User).filter_by(id=7).all():

	send_mail(
		to_address=user.email,
		subject=subject,
		html=html,
		plaintext=content)

    
