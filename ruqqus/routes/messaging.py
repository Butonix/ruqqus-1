from urllib.parse import urlparse
from time import time
import mistletoe

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.get import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.markdown import *
from ruqqus.classes import *
from flask import *
from ruqqus.__main__ import app


@app.route("/new_message", methods=["POST"])
@is_not_banned
@validate_formkey
def create_new_convo(v)

    names=request.form.get("to_users")
    names=names.split(',')
    names=[x.lstrip().rstrip().lstrip('@') for x in names]

    users=[]
    if len(names)>10:
        return jsonify({"error": "You may only include 10 other users in this conversation."}), 400

    for name in names:
        user=get_user(name, graceful=True)

        if user.id==v.id:
            return jsonify({"error":"You can't send messages to yourself."})

        if not user:
            return jsonify({"error": f"No user named @{name}"}), 404

        if v.any_block_exists(user):
            return jsonify({"error": f"You can't send messages to {user.username}."}), 403


    subject=sanitize(request.form.get("subject"))

    new_convo=Conversation(author_id=v.id,
        created_utc=int(time.time()),
        subject=subject
        )

    g.db.add(new_convo)
    g.db.flush()

    message=request.form.get("message")

    with CustomRenderer() as renderer:
        message_md=renderer.render(mistletoe.Document(message))
    message_html=sanitize(messge_md, linkgen=True)

    new_message=Message(author_id=v.id,
        created_utc=new_convo.created_utc,
        body=message,
        body_html=message_html,
        )

    g.db.add(new_message)

    for user in [v]+users:
        new_cm=ConvoMember(user_id=user.id,
            convo_id=new_convo.id)
        g.db.add(new_cm)


    return jsonify({"redirect":new_convo.permalink})


@app.route("/reply_message", methods=["POST"])
@is_not_banned
@validate_formkey
def reply_to_message(v):

    convo_id=request.form.get("convo_id")

    convo=g.db.query(Conversation).get(convo_id)

    if not convo:
        abort(404)

    cm=g.db.query(ConvoMember).filter_by(user_id=v.id, convo_id=convo_id)
    if not cm:
        abort(403)

    message=request.form.get("message")

    with CustomRenderer() as renderer:
        message_md=renderer.render(mistletoe.Document(message))
    message_html=sanitize(messge_md, linkgen=True)

    new_message=Message(author_id=v.id,
        created_utc=int(time.time()),
        body=message,
        body_html=message_html,
        )

    g.db.add(new_message)

    return jsonify({"html":body_html})
