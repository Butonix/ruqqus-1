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


'''
create new conversation
'''

@app.route("/new_message", methods=["POST"])
@is_not_banned
@validate_formkey
def create_new_convo(v):


    names=request.form.get("to_users")
    names=names.split()
    names=[x.lstrip().rstrip().rstrip(',').lstrip('@') for x in names]

    users=[]
    if len(names)>10:
        return jsonify({"error": "You may only include 10 other users in this conversation."}), 400

    for name in names:
        user=get_user(name, v=v, graceful=True)

        if user.id==v.id:
            return jsonify({"error":"You can't send messages to yourself."})

        if not user:
            return jsonify({"error": f"No user named @{name}"}), 404

        if v.any_block_exists(user):
            return jsonify({"error": f"You can't send messages to {user.username}."}), 403


    subject=sanitize(request.form.get("subject").lstrip().rstrip())
    if not subject:
        return jsonify({"error":"Subject required"})

    new_convo=Conversation(author_id=v.id,
        created_utc=int(time.time()),
        subject=subject
        )

    g.db.add(new_convo)
    g.db.flush()

    message=request.form.get("message")

    with CustomRenderer() as renderer:
        message_md=renderer.render(mistletoe.Document(message))
    message_html=sanitize(message_md, linkgen=True)

    new_message=Message(author_id=v.id,
        created_utc=new_convo.created_utc,
        body=message,
        body_html=message_html,
        convo_id=new_convo.id
        )

    g.db.add(new_message)

    for user in [v]+users:
        new_cm=ConvoMember(
            user_id=user.id,
            convo_id=new_convo.id
            )
        g.db.add(new_cm)


    return jsonify({"redirect":new_convo.permalink})


'''
reply to existing conversation
'''

@app.post("/reply_message")
@is_not_banned
@validate_formkey
def reply_to_message(v):

    convo_id=request.form.get("convo_id")

    convo=get_convo(convo_id, v=v)

    message=request.form.get("message")

    with CustomRenderer() as renderer:
        message_md=renderer.render(mistletoe.Document(message))
    message_html=sanitize(messge_md, linkgen=True)

    new_message=Message(author_id=v.id,
        created_utc=int(time.time()),
        body=message,
        body_html=message_html,
        convo_id=convo.id
        )

    g.db.add(new_message)

    return jsonify({"html":body_html})


'''
view conversation
'''

@app.get("/messages/<convo_id>")
@app.get("/messages/<convo_id>/message/<message_id>")
@is_not_banned
def message_perma(v, convo_id, message_id=None):

    convo=get_convo(convo_id, v=v)

    messages = convo.messages.sorted(key=lambda x: x.id)

    if message_id:

        m_id = base36decode(message_id)

        if message_id not in [x.id for x in messages]:
            return redirect(convo.permalink)

        message=[x for x in messages if x.id==m_id][0]

    else:
        message=None

    return render_template("messages.html",
        v=v,
        conversations=[convo],
        message=message
        )

@app.get("/new_message")
@is_not_banned
def new_message(v):

    return render_template(
        "create_convo.html",
        v=v
        )