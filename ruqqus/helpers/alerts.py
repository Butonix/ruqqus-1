import mistletoe

from ruqqus.classes import *
from ruqqus.__main__ import db
from .markdown import *

def send_notification(user, text):

    with CustomRenderer() as renderer:
        text_html=renderer.render(mistletoe.Document(text))

    new_comment=Comment(author_id=1,
                        body=text,
                        body_html=text_html,
                        parent_submission=None,
                        distinguish_level=6,
                        is_offensive=False
                        )
    db.add(new_comment)
    db.commit()
    notif=Notification(comment_id=new_comment.id,
                       user_id=user.id)
    db.add(notif)
    db.commit()
