import os
import logging
import redis
import gevent
import mistletoe
from flask import *
from flask_socketio import *

from ruqqus.helpers.wrappers import get_logged_in_user, auth_required
from ruqqus.helpers.get import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.markdown import CustomRenderer, preprocess
from ruqqus.__main__ import app, socketio, db_session

REDIS_URL = app.config["CACHE_REDIS_URL"]

#app = Flask(__name__)
#app.debug = 'DEBUG' in os.environ


SIDS={}


def socket_auth_required(f):

    def wrapper(*args, **kwargs):

        g.db=db_session()

        v, client=get_logged_in_user()

        if client or not v:
            send("Not logged in")
            return

        f(*args, v, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper

def get_room(f):

    def wrapper(*args, **kwargs):

        data=args[0]
        guild=get_guild(data["guild"])

        if guild.is_banned:
            return

        f(*args, guild, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper

@socketio.on('connect')
def socket_connect_auth_user():

    g.db=db_session()

    v, client=get_logged_in_user()

    if client or not v:
        emit("error", {"error":"Authentication required"})
        disconnect()

    if v.username.lower() in SIDS:
        SIDS[v.id].append(request.sid)
    else:
        SIDS[v.id]=[request.sid]

@socketio.on('disconnect')
@socket_auth_required
def socket_disconnect_user(v):

    for room in rooms():
        leave_room(room)
        send(f"← @{v.username} has left the chat", room=room)




@socketio.on('join room')
@socket_auth_required
@get_room
def join_guild_room(data, v, guild):

    if not guild.can_submit(v):
        send(f"You can't join the +{guild.name} chat right now.")
        return

    join_room(guild.fullname)
    send(f"→ @{v.username} has entered the chat", room=guild.fullname)

@socketio.on('leave room')
@socket_auth_required
@get_room
def leave_guild_room(data, v, guild):
    leave_room(guild.fullname)
    send(f"← @{v.username} has left the chat", room=guild.fullname)


@socketio.on('speak')
@socket_auth_required
@get_room
def speak_guild(data, v, guild):

    text=data['text'][0:1000].lstrip().rstrip()
    if not text:
        return

    text=preprocess(text)
    with CustomRenderer() as renderer:
        text = renderer.render(mistletoe.Document(text))
    text = sanitize(text, linkgen=True)

    data={
        "avatar": v.profile_url,
        "username":v.username,
        "text":text,
        "room": guild.fullname
    }
    emit("speak", data, to=guild.fullname)

    if text.startswith('/') and guild.has_mod(v):
        args=text.split()

        if args[0]=="/kick":
            user=get_user(args[1], graceful=True)
            reason= " ".join(args[2:]) if len(args)>3 else "none"
            if not user:
                send(f"No user named {args[1]}")
            x=False
            for sid in SIDS[user.id]:
                for room in rooms(sid=sid):
                    if room==guild.fullname:
                        if not x:
                            send(f"← @{user.username} kicked by @{v.username}. Reason: {reason} ", to=guild.fullname)
                        leave_room(guild.fullname, sid=sid)
                        x=True
            if not x:
                send(f"User {args[1]} not present in chat")






@app.route("/socket_home")
#@auth_required
def socket_home(v=None):

    return render_template("chat/chat_test.html", v=v)


@app.route("/+<guildname>/chat", methods=["GET"])
@auth_required
def guild_chat(guildname, v):

    guild=get_guild(guildname)

    return render_template("chat/chat.html", b=guild, v=v)