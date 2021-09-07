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

@app.post("/new_message")
@app.post("/api/v2/conversations")
@is_not_banned
@api("messages")
@validate_formkey
def create_new_convo(v):
    
    """
Create a new conversation thread.

Required form data:

* `to` - Space-separated list of users to include. Alternatively, a single guildname beginning with a `+`.
    """

    names=request.form.get("to")
    names=names.split()
    names=[x.lstrip().rstrip().rstrip(',').lstrip('@') for x in names]

    users=[]
    if len(names)>10:
        return jsonify({"error": "You may only include 10 other users in this conversation."}), 400

    if names[0].startswith("+"):
        #it's a modmail

        if len(names)>1:
            return jsonify({"error":f"You can message one Guild or up to 10 users, but not both."})

        board = get_guild(names[0].lstrip('+'))

        if board.is_banned:
            return jsonify({"error":f"+{board.name} is banned and can't receive modmail."})

        for mod in board.moderators:
            if not mod.perm_mail and not mod.perm_full:
                continue

            if mod.user.is_banned or mod.user.is_deleted:
                continue

            users.append(mod.user)

        if not users:
            return jsonify({"error":f"There are no Guildmasters of +{board.name} to receive your message"})

        board_id=board.id


    else:
        for name in names:
            user=get_user(name, v=v, graceful=True)

            if user.id==v.id:
                return jsonify({"error":"You can't send messages to yourself."})

            if not user:
                return jsonify({"error": f"No user named @{name}"}), 404

            if v.any_block_exists(user):
                return jsonify({"error": f"You can't send messages to {user.username}."}), 403

            users.append(user)
        board_id=0


    subject=sanitize(request.form.get("subject").lstrip().rstrip())
    if not subject:
        return jsonify({"error":"Subject required"})

    new_convo=Conversation(author_id=v.id,
        created_utc=int(time.time()),
        subject=subject,
        board_id=board_id
        )

    g.db.add(new_convo)
    g.db.flush()

    message=request.form.get("message")
    if not message:
        g.db.rollback()
        return jsonify({"error":"You need to actually write something!"}), 400

    with CustomRenderer() as renderer:
        message_md=renderer.render(mistletoe.Document(message))
    message_html=sanitize(message_md, linkgen=True)

    new_message=Message(author_id=v.id,
        created_utc=new_convo.created_utc,
        body=message,
        body_html=message_html,
        convo_id=new_convo.id,
        creation_ip = request.remote_addr,
        creation_region = request.headers.get("cf-ipcountry")
        )

    g.db.add(new_message)

    for user in list(set([v]+users)):
        new_cm=ConvoMember(
            user_id=user.id,
            convo_id=new_convo.id
            )
        g.db.add(new_cm)

    g.db.commit()


    return {"html": lambda:redirect(new_convo.permalink),
            "api": lambda:jsonify(new_convo.json)
           }


'''
reply to existing conversation
'''

@app.post("/messages/<cid>/reply")
@app.post("/api/v2/conversations/<cid>/messages")
@is_not_banned
@api("messages")
@validate_formkey
def reply_to_message(v):
    
    """
Add a new message to an existing conversation.

URL path parameters:

* `cid` - The base 36 conversation ID

Required form data:

* `body` - The raw message text

    """

    convo_id=request.form.get("convo_id")

    convo=get_convo(convo_id, v=v)

    message=request.form.get("body")

    if not message:
        return jsonify({"error":"You need to actually write something!"}), 400

    with CustomRenderer() as renderer:
        message_md=renderer.render(mistletoe.Document(message))
    message_html=sanitize(message_md, linkgen=True)

    new_message=Message(author_id=v.id,
        created_utc=int(time.time()),
        body=message,
        body_html=message_html,
        convo_id=convo.id,
        creation_ip = request.remote_addr,
        creation_region = request.headers.get("cf-ipcountry")
        )

    g.db.add(new_message)

    g.db.commit()

    return {"html":lambda:jsonify(
        {"html":render_template(
            "dms.html", 
            m=new_message,
            v=v
            )
        },
        
    ),
            "api":lambda:jsonify(new_message.html)
           }


'''
view conversation
'''

@app.get("/messages/<cid>")
@app.get("/messages/<cid>/<anything>")
@app.get("/api/v2/conversations/<cid>")
def convo_perma(v, cid, anything=None):

    """
Get a conversation.

URL path parameters:

* `cid` - The conversation's base 36 ID.
"""

    convo=get_convo(cid, v=v)

    return {
        "html":lambda:render_template(
            "messages.html",
            v=v,
            convo=convo
            ),
        "api":lambda:jsonify(convo.json)
        }


@app.get("/messages/<cid>/<anything>/<mid>")
@app.get("/api/v2/conversations/<cid>/messages/<mid>")
@is_not_banned
@api("messages", "read")
def message_perma(v, cid, mid, anything=None):

    """
Get a message within a conversation.

URL path parameters:

* `cid` - The conversation's base 36 ID.
* `mid` - The message's base 36 ID.
"""

    convo=get_convo(cid, v=v)

    m_id = base36decode(mid)
    
    message = [x for x in convo.messages if x.id==m_id]

    if not message:
        abort(404)

    message=message[0]

    return {
        "html":lambda:render_template(
            "messages.html",
            v=v,
            convo=convo,
            linked_message=message
            ),
        "api":lambda:jsonify(message.json)
        }

@app.get("/new_message")
@is_not_banned
def new_message(v):


    return render_template(
        "create_convo.html",
        v=v
        )
