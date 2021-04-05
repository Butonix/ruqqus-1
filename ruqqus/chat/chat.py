import os
import logging
import redis
import gevent
from flask import *
from flask_socketio import *

from ruqqus.helpers.wrappers import get_logged_in_user, auth_required
from ruqqus.helpers.get import *
from ruqqus.__main__ import app, socketio, db_session

REDIS_URL = app.config["CACHE_REDIS_URL"]

#app = Flask(__name__)
#app.debug = 'DEBUG' in os.environ



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

@socketio.on('join room')
@socket_auth_required
@get_room
def join_guild_room(data, guild, v):

    if guild.has_ban(v):
        emit("error", {"error":f"You are banned from +{guild.name}"})
        return

    join_room(guild.fullname)
    send(f"→ @{v.username} has entered the chat", room=guild.fullname)

@socketio.on('leave room')
@socket_auth_required
@get_room
def leave_guild_room(data, guild, v):
    leave_room(guild.fullname)
    send(f"← @{v.username} has left the chat", room=guild.fullname)


@socketio.on('speak')
@socket_auth_required
@get_room
def speak_guild(data, guild, v):

    data={
        "username":v.username,
        "text":data["text"]
    }
    emit("speak", data, to=guild.fullname)


@app.route("/socket_home")
#@auth_required
def socket_home(v=None):

    return render_template("chat/chat_test.html", v=v)


@app.route("/+<guildname>/chat", methods=["GET"])
@auth_required
def guild_chat(guildname, v):

    guild=get_guild(guildname)

    return render_template("chat/chat.html", b=guild, v=v)