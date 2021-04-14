import os
import redis
import mistletoe
from flask import *
from flask_socketio import *
import random
from sqlalchemy.orm import lazyload
import time
import secrets

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.get import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.session import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.markdown import CustomRenderer, preprocess
from ruqqus.helpers.aws import *
from ruqqus.__main__ import app, r, socketio, db_session

REDIS_URL = app.config["CACHE_REDIS_URL"]
BUCKET=app.config["S3_BUCKET"]

#app = Flask(__name__)
#app.debug = 'DEBUG' in os.environ


SIDS={}

COMMANDS={}
HELP={}

TYPING={}

def now():

    return time.strftime("%d %b %Y at %H:%M:%S", time.gmtime(int(time.time())))


def command(c, syntax=""):

    def wrapper_maker(f):

        if c in COMMANDS:
            raise ValueError(f"Duplicate command `{c}`")

        #if f.__name__ in [x.__name__ for x in COMMANDS.values()]:
        #    raise ValueError(f"Duplicate command function {f.__name__}")

        COMMANDS[c]=f
        HELP[c]=syntax

        def wrapper(*args, **kwargs):
            f(*args, **kwargs)

        wrapper.__name__=f.__name__
        wrapper.__doc__=f.__doc__
        return wrapper

    return wrapper_maker

def gm_command(f):

    def wrapper(*args, **kwargs):

        guild=kwargs['guild']
        v=kwargs['v']

        if not guild.has_mod(v, "chat"):
            send(f"You do not have permission to use the {args[0][0]} command in this channel.")
            return

        f(*args, **kwargs)
        

    wrapper.__name__=f.__name__
    wrapper.__doc__=f.__doc__
    return wrapper

def admin_command(f):

    def wrapper(*args, **kwargs):

        v=kwargs['v']

        if v.admin_level <4:
            send(f"You do not have permission to use the {args[0][0]} command.")
            return

        f(*args, **kwargs)
        

    wrapper.__name__=f.__name__
    wrapper.__doc__=f.__doc__
    return wrapper

def speak(text, user, guild, as_guild=False):

    if isinstance(text, list):
        text=" ".join(text)

    text=preprocess(text)
    with CustomRenderer() as renderer:
        text = renderer.render(mistletoe.Document(text))
    text = sanitize(text, linkgen=True)

    if as_guild:
        data={
            "avatar": guild.profile_url,
            "username":guild.name,
            "text":text,
            "room": guild.fullname,
            "guild": guild.name,
            "time": now()
        }
        emit("motd", data, to=guild.fullname)
    else:
        data={
            "avatar": user.profile_url,
            "username":user.username,
            "text":text,
            "room": guild.fullname,
            "guild": guild.name,
            "time": now()
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

        g.v=v

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
        send("Authentication required")
        disconnect()
        return

    if v.is_suspended:
        send("You're banned and can't access chat right now.")
        disconnect()
        return

    if v.id in SIDS:
        SIDS[v.id].append(request.sid)
    else:
        SIDS[v.id]=[request.sid]

    g.db.close()
    g.v=v

    emit("status", {'status':"connected"})

@socketio.on('disconnect')
@socket_auth_required
def socket_disconnect_user(v):

    try:
        SIDS[v.id].remove(request.sid)
    except ValueError:
        pass

    for room in rooms():
        leave_room(room)
        if room not in v_rooms(v):
            send(f"← @{v.username} has left the chat", to=room)

        board=get_from_fullname(room, graceful=True)
        if board:
            update_chat_count(board)

            if v.username in TYPING.get(board.fullname, []):
                TYPING[board.fullname].remove(v.username)
                emit('typing', {'users':TYPING[board.fullname]}, to=board.fullname)





@socketio.on('join room')
@socket_auth_required
@get_room
def join_guild_room(data, v, guild):

    if not guild.can_chat(v):
        send(f"You can't join #{guild.name} right now.")
        return False

    broadcast= guild.fullname not in v_rooms(v)

    join_room(guild.fullname)
    update_chat_count(guild)
    if broadcast:
        send(f"→ @{v.username} has entered the chat", to=guild.fullname)

    if guild.motd:

        data={
            "avatar": guild.profile_url,
            "username":guild.name,
            "text":guild.motd,
            "room":guild.fullname,
            "guild":guild.name,
            "time": now()
            }
        emit('motd', data, to=request.sid)

    return True

@socketio.on('leave room')
@socket_auth_required
@get_room
def leave_guild_room(data, v, guild):
    leave_room(guild.fullname)
    update_chat_count(guild)

    if guild.fullname not in v_rooms(v):
        send(f"← @{v.username} has left the chat", to=guild.fullname)

    if v.username in TYPING.get(guild.fullname, []):
        TYPING[guild.fullname].remove(v.username)
        emit('typing', {'users':TYPING[guild.fullname]}, to=guild.fullname)

    emit("status", {'status':f"Left #{guild.name}"})

@socketio.on('speak')
@socket_auth_required
@get_room
def speak_guild(data, v, guild):

    if guild.fullname not in rooms():
        send(f"You aren't connected to #{guild.name}. Trying to join...")
        x=join_guild_room(data)
        if not x:
            return

    if v.username in TYPING.get(guild.fullname, []):
        TYPING[guild.fullname].remove(v.username)
        emit('typing', {'users':TYPING[guild.fullname]}, to=guild.fullname)


    raw_text=data['text'][0:1000].lstrip().rstrip()
    if not raw_text:
        return
    
    user_pad=" "*(25-len(v.username))
    guild_pad=" "*(25-len(guild.name))
    print(f"@{v.username}{user_pad} - #{guild.name}{guild_pad} - {raw_text}")

    if raw_text.startswith('/'):
        args=raw_text.split()
        command=args[0].lstrip('/')
        if command in COMMANDS:
            COMMANDS[command](args, guild=guild, v=v)
        else:
            send(f"Command `{command}` not recognized")

    else:
        speak(raw_text, v, guild)

@socketio.on('typing')
@socket_auth_required
@get_room
def typing_indicator(data, v, guild):

    #guild in typing
    if guild.fullname not in TYPING:
        TYPING[guild.fullname]=[]

    if guild.fullname not in v_rooms(v):
        return

    if data['typing'] and v.username not in TYPING[guild.fullname]:
        TYPING[guild.fullname].append(v.username)
    elif not data['typing'] and v.username in TYPING[guild.fullname]:
        TYPING[guild.fullname].remove(v.username)

    emit('typing', {'users':TYPING[guild.fullname]}, to=guild.fullname)





##############
#            #
#   ROUTES   #
#            #
##############



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
        return render_template(
            "errors/nsfw.html",
            v=v,
            t=t,
            lo_formkey=make_logged_out_formkey(t),
            board=board
            )

    return render_template(
        "chat/chat.html", 
        b=board, 
        v=v,
        is_subscribed=(v and board.has_subscriber(v))
        )


##############
#            #
#  COMMANDS  #
#            #
##############

@command('part')
@command('leave')
def leave_room_command(args, guild, v):

    """Leave the chat channel"""

    send(f"← @{v.username} has left the chat", to=guild.fullname)

    for sid in SIDS[v.id]:
        leave_room(guild.fullname, sid=sid)
        emit('typing',{'users':[]}, to=sid)

@command('help', syntax='[command]')
def help_command(args, guild, v):

    """Displays help information for a command, or displays a list of commands if no command is provided."""
    if len(args)>1:
        target=args[1]
        if target in COMMANDS:
            send(f"/{target}{' '+HELP[target] if HELP[target] else ''} - {COMMANDS[target].__doc__}")
        else:
            send(f"Unknown command `{target}`")
    else:
        commands=[x for x in COMMANDS.keys()]
        commands=sorted(commands)
        send(f"Type `/help <command>` for information on a specific command. Commands: {', '.join(commands)}")

@command('ruqqie')
def print_ruqqie(args, guild, v):
    """Prints an ascii Ruqqie"""

    data={
        "avatar": v.profile_url,
        "username":v.username,
        "text":'<pre class="text-black">  👑<br>  ╭───────╮<br> ╭┤  ╹ ╹  ├╮<br>  ╰─┬───┬─╯</pre>',
        "room": guild.fullname,
        "guild": guild.name,
        "time": now()
    }
    if request.headers.get("X-User-Type")=="Bot":
        emit("bot", data, to=guild.fullname)
    else:
        emit("speak", data, to=guild.fullname)


@command('random')
def random_post(args, guild, v):

    """Fetches a random post from this channel's Guild."""

    total=g.db.query(Submission).options(lazyload('*')).filter_by(board_id=guild.id, deleted_utc=0, is_banned=False).count()
    offset=random.randint(0, total-1)
    post=g.db.query(Submission).options(lazyload('*')).filter_by(board_id=guild.id, deleted_utc=0, is_banned=False).order_by(Submission.id.asc()).offset(offset).first()
    speak(f"Random Post: <a href=\"https://{app.config['SERVER_NAME']}{post.permalink}\">{post.title}</a>", v, guild)



@command('shrug', syntax='[text]')
def shrug(args, guild, v):
    """Appends ¯\\_(ツ)_/¯ to your chat message."""
    args.append(r"¯\\\_(ツ)_/¯")
    speak(args[1:], v, guild)

@command('lenny', syntax='[text]')
def lenny(args, guild, v):
    """Appends ( ͡° ͜ʖ ͡°) to your chat message."""
    args.append("( ͡° ͜ʖ ͡°)")
    speak(args[1:], v, guild)

@command('table', syntax='[text]')
def table(args, guild, v):
    """Appends (╯° □°） ╯︵ ┻━┻ to your chat message."""
    args.append("(╯° □°） ╯︵ ┻━┻")
    speak(args[1:], v, guild)

@command('untable', syntax='[text]')
def untable(args, guild, v):
    """Appends ┬─┬ノ( º _ ºノ)to your chat message."""
    args.append('┬─┬ノ( º _ ºノ)')
    speak(args[1:], v, guild)

@command('porter', syntax='[text]')
def porter(args, guild, v):
    """Appends 【=◈︿◈=】 to your chat message."""
    args.append('【=◈︿◈=】')
    speak(args[1:], v, guild)

@command('notsure', syntax='[text]')
def notsure(args, guild, v):
    """Appends (≖_≖ ) to your chat message."""
    args.append('(≖_≖ )')
    speak(args[1:], v, guild)

@command('flushed', syntax='[text]')
def flushed(args, guild, v):
    """Appends ◉_◉ to your chat message."""
    args.append('◉_◉')
    speak(args[1:], v, guild)

@command('gib', syntax='[text]')
def gib(args, guild, v):
    """Appends ༼ つ ◕_◕ ༽つ to your chat message."""
    args.append('༼ つ ◕_◕ ༽つ')
    speak(args[1:], v, guild)

@command('sus', syntax='[text]')
def sus(args, guild, v):
    """Appends one of the following to your chat message:  ඞඞ  ඣ  යඞ"""
    args.append(random.choice(['ඞඞ','ඣ','යඞ']))
    speak(args[1:], v, guild)

@command('here')
def here_command(args, guild, v):
    """Displays a list of users currently present in the chat."""
    ids=set()
    for uid in SIDS:
        for sid in SIDS[uid]:
            if guild.fullname in rooms(sid=sid):
                ids.add(uid)
                break

    users=g.db.query(User.username).filter(User.id.in_(tuple(ids))).all()
    names=[x[0] for x in users]
    names=sorted(names)

    #typing clearer
    for name in TYPING[guild.fullname]:
        if name not in names:
            TYPING[guild.fullname].remove(name)
            emit('typing',{'users':TYPING[guild.fullname]}, to=guild.fullname)


    count=len(names)
    namestr = ", ".join(names)
    send(f"{count} user{'s' if count>1 else ''} present: {namestr}")

@command('me', syntax="<text>")
def me_action(args, guild, v):
    """Sends your message as an action."""
    text=" ".join(args[1:])
    if not text:
        return
    text=sanitize(text, linkgen=False)
    emit('me', {'msg':f"@{v.username} {text}"}, to=guild.fullname)
    return

@command('kick', syntax="<username> [reason]")
@gm_command
def kick_user(args, guild, v):
    """Ejects a user from the chat. They can rejoin immediately. (Must be Guildmaster.)"""
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
                if user.username in TYPING.get(guild.fullname, []):
                    TYPING[guild.fullname].remove(user.username)
                    emit('typing', {'users':TYPING[guild.fullname]}, to=guild.fullname)

                x=True

@command('ban', syntax="<username> [reason]")
@gm_command
def chatban_user(args, guild, v):
    """Ejects a user from the chat. They may not rejoin until unbanned. (Must be Guildmaster.)"""
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
    for sid in SIDS.get(user.id,[]):
        for room in rooms(sid=sid):
            if room==guild.fullname:
                if not x:
                    send(f"← @{user.username} kicked and banned by @{v.username}.{' Reason: '+reason if reason else ''}", to=guild.fullname)
                    x=True
                leave_room(guild.fullname, sid=sid)
                update_chat_count(guild)
                if user.username in TYPING.get(guild.fullname, []):
                    TYPING[guild.fullname].remove(user.username)
                    emit('typing', {'users':TYPING[guild.fullname]}, to=guild.fullname)

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

@command('gm', syntax="<text>")
@gm_command
def speak_as_gm(args, guild, v):
    """Distinguish your message with a Guildmaster's crown. (Must be Guildmaster.)"""
    text=" ".join(args[1:])
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
        "room":guild.fullname,
        "guild":guild.name,
        "time": now()
        }
    emit('gm', data, to=guild.fullname)

@command('unban', syntax="<username>")
@gm_command
def un_chatban_user(args, guild, v):
    """Unban a banned user from this chat. (Must be Guildmaster.)"""
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

@command('motd', syntax="[text]")
@gm_command
def message_of_the_day(args, guild, v):
    """Set or clear a Message of the Day, to be shown to users upon joining this channel. Messages are shown as being spoken by the guild. (Must be Guildmaster.)"""

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
            "room":guild.fullname,
            "guild":guild.name,
            "time": now()
            }
        emit('motd', data, to=request.sid)

    else:
        guild.motd=''
        g.db.add(guild)
        g.db.commit()
        send("Message removed")


@command('admin', syntax="<text>")
@admin_command
def speak_admin(args, guild, v):
    """Distinguish your message with an Administrator's shield. (Must be site administrator.)"""


    text=" ".join(args[1:])
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
        'guild':guild.name,
        'room':guild.fullname,
        "time": now()
        }
    emit('admin', data, to=guild.fullname)


@command('wallop', syntax="<text>")
@admin_command
def wallop(args, guild, v):
    """Send a global broadcast. (Must be site administrator.)"""
    text=" ".join(args[1:])
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
        "time": now()
        }

    sent=[]
    for uid in SIDS:
        for sid in SIDS[uid]:
            for roomid in rooms(sid=sid):
                if roomid.startswith('t4_') and roomid not in sent:
                    emit('wallop', data, to=roomid)
                    sent.append(roomid)

@command('say', syntax="<text>")
@gm_command
def say_guild(args, guild, v):
    """Say something as the Guild. (Must be Guildmaster.)"""

    text=" ".join(args[1:])
    text=preprocess(text)
    with CustomRenderer() as renderer:
        text = renderer.render(mistletoe.Document(text))
    text = sanitize(text, linkgen=True)

    data={
        "avatar": guild.profile_url,
        "username":guild.name,
        "text":text,
        "time": now()
        }
    emit('motd', data, to=guild.fullname)

@command('msg', syntax="<username> <text>")
def direct_message(args, guild, v):
    """Send someone a private message. Use Tab to reply to the most recent private message"""

    if len(args)<3:
        send("Not enough arguments. Type `/help msg` for more information.")
        return

    user=get_user(args[1], graceful=True)
    if not user:
        send(f"No user named @{args[1]}.")
        return

    targets=SIDS.get(user.id, [])
    if (not targets) or v.any_block_exists(user):
        send(f"@{user.username} is not online right now.")
        return

    text=" ".join(args[2:])

    text=preprocess(text)
    with CustomRenderer() as renderer:
        text = renderer.render(mistletoe.Document(text))
    text = sanitize(text, linkgen=True)

    t=now()

    data={
        "avatar": v.profile_url,
        "username":v.username,
        "text":text,
        "time": t
        }

    for sid in targets:
        emit('msg-in', data, to=sid)

    data={
        "avatar": v.profile_url,
        "username":user.username,
        "text":text,
        "time": t
        }
    for sid in SIDS.get(v.id,[]):
        emit('msg-out', data, to=sid)

##############
#            #
#  PICTURES  #
#            #
##############


@app.route("/chat_upload", methods=["POST"])
@is_not_banned
def chat_upload_image(v):

    if not v.has_premium:
        abort(403)


    file = request.files['image']
    if not file.content_type.startswith('image/'):
        abort(400)

    now=int(time.time())
    now=base36encode(now)
    name = f'chat/{now}/{secrets.token_urlsafe(8)}'
    upload_file(name, file)

    check_csam_url(f"https://{BUCKET}/{name}", v, lambda:delete_file(name))

    return jsonify({'url':f"https://{BUCKET}/{name}"})