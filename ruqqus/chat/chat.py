import os
import logging
import redis
import gevent
import mistletoe
from flask import *
from flask_socketio import *
import random

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.get import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.session import *
from ruqqus.helpers.markdown import CustomRenderer, preprocess
from ruqqus.__main__ import app, r, socketio, db_session

REDIS_URL = app.config["CACHE_REDIS_URL"]

#app = Flask(__name__)
#app.debug = 'DEBUG' in os.environ


SIDS={}

COMMANDS={}


def command(c):

    def wrapper_maker(f):

        if c in COMMANDS:
            raise ValueError(f"Duplicate command `{c}`")

        if f.__name__ in [x.__name__ for x in COMMANDS.values()]:
            raise ValueError(f"Duplicate command function {f.__name__}")

        COMMANDS[c]=f

        def wrapper(*args, **kwargs):

            f(*args, **kwargs)

        wrapper.__name__=f.__name__
        return wrapper

    return wrapper_maker

def gm_command(f):

    def wrapper(*args, **kwargs):

        guild=kwargs['guild']
        v=kwargs['v']

        if not guild.has_mod(v, "chat"):
            send(f"You do not have permission to use the {args[0]} command in this channel.")
            return

        f(*args, **kwargs)
        

    wrapper.__name__=f.__name__
    return wrapper

def admin_command(f):

    def wrapper(*args, **kwargs):

        v=kwargs['v']

        if v.admin_level <4:
            send(f"You do not have permission to use the {args[0]} command.")
            return

        f(*args, **kwargs)
        

    wrapper.__name__=f.__name__
    return wrapper

def speak(text, user, guild):

    if isinstance(text, list):
        text=" ".join(text)

    text=preprocess(text)
    with CustomRenderer() as renderer:
        text = renderer.render(mistletoe.Document(text))
    text = sanitize(text, linkgen=True)

    data={
        "avatar": user.profile_url,
        "username":user.username,
        "text":text,
        "room": guild.fullname
    }
    if request.headers.get("X-User-Type")=="Bot":
        emit("bot", data, to=guild.fullname)
    else:
        emit("speak", data, to=guild.fullname)
    return

def v_rooms(v):

    output=[]
    for sid in SIDS.get(v.id,[]):
        for room in rooms(sid=sid):
            if room not in output:
                output.append(room)
    return output

def update_chat_count(board):

    count=[]
    for uid in SIDS:
        for sid in SIDS[uid]:
            for room in rooms(sid=sid):
                if room==board.fullname and uid not in count:
                    count.append(uid)
                    break

    count=len(count)

    r.set(f"{board.fullname}_chat_count", count)

    emit("count", {"count":str(count)}, to=board.fullname)

def socket_auth_required(f):

    def wrapper(*args, **kwargs):

        g.db=db_session()

        v, client=get_logged_in_user()

        if client or not v:
            send("Not logged in")
            return

        if v.is_suspended:
            send("You're banned and can't access chat right now.")

        if request.sid not in SIDS.get(v.id, []):
            if v.id in SIDS:
                SIDS[v.id].append(request.sid)
            else:
                SIDS[v.id]=[request.sid]

        f(*args, v, **kwargs)

        g.db.close()

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

    if v.is_suspended:
        send("You're banned and can't access chat right now.")

    if v.id in SIDS:
        SIDS[v.id].append(request.sid)
    else:
        SIDS[v.id]=[request.sid]

    print(f"{v.username} connected")
    g.db.close()

@socketio.on('disconnect')
@socket_auth_required
def socket_disconnect_user(v):

    try:
        SIDS[v.id].remove(request.sid)
    except ValueError:
        pass

    for room in rooms():
        leave_room(room)
        send(f"← @{v.username} has left the chat", to=room)
        board=get_from_fullname(room, graceful=True)
        if board:
            update_chat_count(board)




@socketio.on('join room')
@socket_auth_required
@get_room
def join_guild_room(data, v, guild):

    if not guild.can_chat(v):
        send(f"You can't join the +{guild.name} chat right now.")
        return False

    join_room(guild.fullname)
    update_chat_count(guild)

    send(f"→ @{v.username} has entered the chat", to=guild.fullname)

    if guild.motd:

        data={
            "avatar": guild.profile_url,
            "username":guild.name,
            "text":guild.motd,
            "guild":guild.name
            }
        emit('motd', data, to=request.sid)
    return True

@socketio.on('leave room')
@socket_auth_required
@get_room
def leave_guild_room(data, v, guild):
    leave_room(guild.fullname)
    update_chat_count(guild)
    send(f"← @{v.username} has left the chat", to=guild.fullname)


@socketio.on('speak')
@socket_auth_required
@get_room
def speak_guild(data, v, guild):

    if guild.fullname not in rooms():
        send("You aren't connected to that chat room. Trying to join...")
        x=join_guild_room(data)
        if not x:
            return

    raw_text=data['text'][0:1000].lstrip().rstrip()
    if not raw_text:
        return

    if raw_text.startswith('/'):
        args=raw_text.split()
        args[0].lstrip('/')
        command=args[0]
        if command in COMMANDS:
            COMMANDS[command](args, guild=guild, v=v)
        else:
            send(f"Command `{args[0]}` not recognized")

    else:
        speak(raw_text, v, guild)

@command('shrug')
def shrug(args, guild, v):
    args.append(r"¯\\\_(ツ)_/¯")
    speak(args[1:], v, guild)

@command('lenny')
def lenny(args, guild, v):
    args.append("( ͡° ͜ʖ ͡°)")
    speak(args[1:], v, guild)

@command('table')
def table(args, guild, v):
    args.append("(╯° □°） ╯︵ ┻━┻")
    speak(args[1:], v, guild)

@command('untable')
def untable(args, guild, v):
    args.append('┬─┬ノ( º _ ºノ)')
    speak(args[1:], v, guild)

@command('porter')
def porter(args, guild, v):
    args.append('【=◈︿◈=】')
    speak(args[1:], v, guild)

@command('notsure')
def notsure(args, guild, v):
    args.append('(≖_≖ )')
    speak(args[1:], v, guild)

@command('flushed')
def flushed(args, guild, v):
    args.append('◉_◉')
    speak(args[1:], v, guild)

@command('gib')
def gib(args, guild, v):
    args.append('༼ つ ◕_◕ ༽つ')
    speak(args[1:], v, guild)

@command('sus')
def sus(args, guild, v):
    args.append(random.choice(['ඞඞ','ඣ','යඞ']))
    speak(args[1:], v, guild)

@command('here')
def here_command(args, guild, v):
    ids=set()
    for uid in SIDS:
        for sid in SIDS[uid]:
            if guild.fullname in rooms(sid=sid):
                ids.add(uid)
                break

    users=g.db.query(User.username).filter(User.id.in_(tuple(ids))).all()
    names=[x[0] for x in users]
    names=sorted(names)
    count=len(names)
    namestr = ", ".join(names)
    send(f"{count} user{'s' if count>1 else ''} present: {namestr}")

@command('me')
def me_action(args, guild, v):
    text=" ".join(args[1:])
    if not text:
        return
    text=sanitize(text, linkgen=False)
    emit('me', {'msg':f"@{v.username} {text}"}, to=guild.fullname)
    return

@command('kick')
@gm_command
def kick_user(args, guild, v):
    user=get_user(args[1], graceful=True)

    if not user:
        send(f"No user named {args[1]}")
        return

    if user.id==v.id:
        send("You can't kick yourself!")
        return
    elif guild.has_mod(user):
        send(f"You can't kick other guildmasters")
        return
    elif guild.has_contributor(user):
        send(f"@{user.username} is an approved contributor and can't currently be kicked.")
        return

    reason= " ".join(args[2:]) if len(args)>=3 else ""

    x=False
    for sid in SIDS[user.id]:
        for room in rooms(sid=sid):
            if room==guild.fullname:
                if not x:
                    send(f"← @{user.username} kicked by @{v.username}. Reason: {reason} ", to=guild.fullname)
                leave_room(guild.fullname, sid=sid)
                update_chat_count(guild)
                x=True

@command('ban')
@gm_command
def chatban_user(args, guild, v):
    user=get_user(args[1], graceful=True)

    if not user:
        send(f"No user named {args[1]}")
        return
    if user.id==v.id:
        send("You can't ban yourself!")
        return
    elif guild.has_mod(user):
        send(f"You can't ban other guildmasters")
        return
    elif guild.has_contributor(user):
        send(f"@{user.username} is an approved contributor and can't currently be banned.")
        return

    existing = g.db.query(ChatBan).filter_by(board_id=guild.id, user_id=user.id).first()

    if existing:
        send(f"@{user.username} is already banned from chat.")
        return

    reason= " ".join(args[2:]) if len(args)>=3 else ""

    x=False
    for sid in SIDS[user.id]:
        for room in rooms(sid=sid):
            if room==guild.fullname:
                if not x:
                    send(f"← @{user.username} kicked and banned by @{v.username}.{' Reason: '+reason if reason else ''}", to=guild.fullname)
                    x=True
                leave_room(guild.fullname, sid=sid)
                update_chat_count(guild)

    if not x:
        send(f"@{user.username} banned by @{v.username}.{' Reason: '+reason if reason else ''}", to=guild.fullname)

    new_ban = ChatBan(
        user_id=user.id,
        board_id=guild.id,
        banning_mod_id=v.id,
        )
    g.db.add(new_ban)

    ma=ModAction(
        kind="chatban_user",
        user_id=v.id,
        target_user_id=user.id,
        board_id=guild.id
        )
    g.db.add(ma)
    g.db.commit()

@command('gm')
@gm_command
def speak_as_gm(args, guild, v):
    text=" ".join(args[1:])
    text=preprocess(text)
    with CustomRenderer() as renderer:
        text = renderer.render(mistletoe.Document(text))
    text = sanitize(text, linkgen=True)

    data={
        "avatar": v.profile_url,
        "username":v.username,
        "text":text
        }
    emit('gm', data, to=guild.fullname)

@command('unban')
@gm_command
def un_chatban_user(args, guild, v):
    user=get_user(args[1], graceful=True)

    if not user:
        send(f"No user named {args[1]}")
        return

    ban=g.db.query(ChatBan).filter_by(board_id=guild.id, user_id=user.id).first()
    if not ban:
        send(f"User {user.username} is not banned from chat.")
        return

    g.db.delete(ban)

    ma=ModAction(
        kind="unchatban_user",
        user_id=v.id,
        target_user_id=user.id,
        board_id=guild.id
        )
    g.db.add(ma)
    g.db.commit()
    send(f"@{user.username} un-chatbanned by @{v.username}.", to=guild.fullname)

@command('motd')
@gm_command
def message_of_the_day(args, guild, v):
    if len(args)>=2:

        message = " ".join(args[1:])
        message=preprocess(message)
        with CustomRenderer() as renderer:
            message = renderer.render(mistletoe.Document(message))
        message = sanitize(message, linkgen=True)

        guild.motd=message
        g.db.add(guild)
        g.db.commit()

        send("Message updated")
        data={
            "avatar": guild.profile_url,
            "username":guild.name,
            "text":guild.motd,
            "guild":guild.name
            }
        emit('motd', data, to=request.sid)

    else:
        guild.motd=''
        g.db.add(guild)
        g.db.commit()
        send("Message removed")


@command('admin')
@admin_command
def speak_admin(args, guild, v):
    text=" ".join(args[1:])
    text=preprocess(text)
    with CustomRenderer() as renderer:
        text = renderer.render(mistletoe.Document(text))
    text = sanitize(text, linkgen=True)

    data={
        "avatar": v.profile_url,
        "username":v.username,
        "text":text
        }
    emit('admin', data, to=guild.fullname)


@command('wallop')
@admin_command
def wallop(args, guild, v):
    text=" ".join(args[1:])
    text=preprocess(text)
    with CustomRenderer() as renderer:
        text = renderer.render(mistletoe.Document(text))
    text = sanitize(text, linkgen=True)

    data={
        "avatar": v.profile_url,
        "username":v.username,
        "text":text
        }

    sent=[]
    for uid in SIDS:
        for sid in SIDS[uid]:
            for roomid in rooms(sid=sid):
                if roomid.startswith('t4_') and roomid not in sent:
                    emit('wallop', data, to=roomid)
                    sent.append(roomid)



@app.route("/socket_home")
#@auth_required
def socket_home(v=None):

    return render_template("chat/chat_test.html", v=v)


@app.route("/+<guildname>/chat", methods=["GET"])
@is_not_banned
def guild_chat(guildname, v):



    board=get_guild(guildname)


    if board.over_18 and not (v and v.over_18) and not session_over18(board):
        t = int(time.time())
        return render_template("errors/nsfw.html",
                                                v=v,
                                                t=t,
                                                lo_formkey=make_logged_out_formkey(t),
                                                board=board
                                                )

    return render_template("chat/chat.html", b=board, v=v)

