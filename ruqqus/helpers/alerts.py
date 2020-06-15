import mistletoe

from ruqqus.classes import *
from flask import g
from .markdown import *
from .sanitize import *

from ruqqus.__main__ import make_session

def send_notification(user, text):

    session=make_session()

    session.begin()

    with CustomRenderer() as renderer:
        text_html=renderer.render(mistletoe.Document(text))

    text_html=sanitize(text_html, linkgen=True)

    new_comment=Comment(author_id=1,
                        body=text,
                        body_html=text_html,
                        parent_submission=None,
                        distinguish_level=6,
                        is_offensive=False
                        )
    session.add(new_comment)
    
    notif=Notification(comment_id=new_comment.id,
                       user_id=user.id)
    session.add(notif)
    
    session.commit()
