import os
import logging
import redis
import gevent
from flask import *
from flask_socketio import *

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.get import *
from ruqqus.__main__ import app, socketio

REDIS_URL = app.config["CACHE_REDIS_URL"]

#app = Flask(__name__)
#app.debug = 'DEBUG' in os.environ

redis = redis.from_url(REDIS_URL)


def socket_auth_required(f):

    def wrapper(*args, **kwargs):

        v, client=get_logged_in_user()

        if client or not v:
            send("Not logged in")
            return

        f(*args, v, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper


@socketio.on('connect')
@socket_auth_required
def socket_connect_auth_user(v):

    if not v:
        disconnect()

@socketio.on('join room')
@socket_auth_required
def join_room(data):

    guild=get_guild(data["guild"])
    if guild.has_ban(v):
        emit("error", {"error":f"You are banned from +{guild.name}"})
        return

    join_room(guild.fullname)

@socketio.on('leave room')
@socket_auth_required
def leave_room(data, v):
    leave_room(data["guild"]):


@app.route("/socket_home")
#@auth_required
def socket_home(v=None):

    return render_template("chat/chat_test.html", v=v)

