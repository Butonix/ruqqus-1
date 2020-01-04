from urllib.parse import urlparse
import mistletoe
import re
import sass

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.markdown import *
from ruqqus.helpers.get import *
from ruqqus.helpers.alerts import *
from ruqqus.classes import *
from .front import guild_ids
from flask import *
from ruqqus.__main__ import app, db, limiter, cache

valid_board_regex=re.compile("^\w{3,25}$")

@app.route("/create_guild", methods=["GET"])
@is_not_banned
def create_board_get(v):
    if not v.is_activated:
        return render_template("message.html", title="Unable to make board", text="You need to verify your email adress first.")
    if v.karma<100:
        return render_template("message.html", title="Unable to make board", text="You need more rep to do that.")

        
    return render_template("make_board.html", v=v)

@app.route("/api/board_available/<name>", methods=["GET"])
def api_board_available(name):
    if db.query(Board).filter(Board.name.ilike(name)).first():
        return jsonify({"board":name, "available":False})
    else:
        return jsonify({"board":name, "available":True})

@app.route("/create_guild", methods=["POST"])
@is_not_banned
@validate_formkey
def create_board_post(v):

    board_name=request.form.get("name")
    board_name=board_name.lstrip("+")

    if not re.match(valid_board_regex, board_name):
        return render_template("message.html", title="Unable to make board", text="Valid board names are 3-25 letters or numbers.")

    if not v.is_activated:
        return render_template("message.html", title="Unable to make board", text="Please verify your email first")

    if v.karma<100:
        return render_template("message.html", title="Unable to make board", text="You need more rep to do that")


    #check name
    if db.query(Board).filter(Board.name.ilike(board_name)).first():
        abort(409)

    #check # recent boards made by user
    cutoff=int(time.time())-60*60*24
    recent=db.query(Board).filter(Board.creator_id==v.id, Board.created_utc >= cutoff).all()
    if len([x for x in recent])>=2:
        abort(429)

    description = request.form.get("description")

    with CustomRenderer() as renderer:
        description_md=renderer.render(mistletoe.Document(description))
    description_html=sanitize(description_md, linkgen=True)

    #make the board

    new_board=Board(name=board_name,
                    description=description,
                    description_html=description_html,
                    over_18=bool(request.form.get("over_18","")),
                    creator_id=v.id
                    )

    db.add(new_board)
    db.commit()

    #add user as mod
    mod=ModRelationship(user_id=v.id,
                        board_id=new_board.id,
                        accepted=True)
    db.add(mod)

    #add subscription for user
    sub=Subscription(user_id=v.id,
                     board_id=new_board.id)
    db.add(sub)
    db.commit()

    #clear cache
    cache.delete_memoized(guild_ids, sort="new")

    return redirect(new_board.permalink)

@app.route("/board/<name>", methods=["GET"])
@app.route("/+<name>", methods=["GET"])
@auth_desired
def board_name(name, v):

    board=get_guild(name)

    if not board.name==name:
        return redirect(board.permalink)

    if board.over_18 and not (v and v.over_18):
        abort(451)

    sort=request.args.get("sort","hot")
    page=int(request.args.get("page", 1))
             
    return board.rendered_board_page(v=v,
                                     sort=sort,
                                     page=page)

@app.route("/mod/kick/<bid>/<pid>", methods=["POST"])
@auth_required
@is_guildmaster
@validate_formkey
def mod_kick_bid_pid(bid,pid, board, v):

    post = get_post(pid)

    if not post.board_id==board.id:
        abort(422)

    if not board.has_mod(v):
        abort(403)

    post.board_id=1
    db.add(post)
    db.commit()

    cache.delete_memoized(Board.idlist, board)

    return "", 204

@app.route("/mod/ban/<bid>/<username>", methods=["POST"])
@auth_required
@is_guildmaster
@validate_formkey
def mod_ban_bid_user(bid, username, board, v):

    user=get_user(username)

    if not board.has_mod(v):
        abort(403)

    if board.has_ban(user):
        abort(409)

    if board.has_mod(user):
        abort(409)

    #you can only exile a user who has previously participated in the guild
    if not (db.query(Submission).filter_by(author_id=user.id, board_id=board.id).first() or
        db.query(Comment).filter(Comment.author_id==user.id, Comment.board_id==board.id).first()):
        abort(400)

    #check for an existing deactivated ban
    existing_ban=db.query(BanRelationship).filter_by(user_id=user.id, board_id=board.id, is_active=False).first()
    if existing_ban:
        existing_ban.is_active=True
        existing_ban.banning_mod_id=v.id
        db.add(existing_ban)
    else:
        new_ban=BanRelationship(user_id=user.id,
                                board_id=board.id,
                                banning_mod_id=v.id,
                                is_active=True)
        db.add(new_ban)


        text=f"You have been exiled from +{board.name}.\n\nNone of your existing posts or comments have been removed, however, you will not be able to make any new posts or comments in +{board.name}."
        send_notification(user, text)
            
    db.commit()

    return "", 204
    
@app.route("/mod/unban/<bid>/<username>", methods=["POST"])
@auth_required
@is_guildmaster
@validate_formkey
def mod_unban_bid_user(bid, username, board, v):

    user=get_user(username)

    x= board.has_ban(user)
    if not x:
        abort(409)

    x.is_active=False

    db.add(x)
    db.commit()
    
    return "", 204

@app.route("/user/kick/<pid>", methods=["POST"])
@auth_required
@validate_formkey
def user_kick_pid(pid, v):

    #allows a user to yank their content back to +general if it was there previously
    
    post=get_post(pid)

    current_board=post.board

    if not post.author_id==v.id:
        abort(403)

    if post.board_id==post.original_board_id:
        abort(403)

    if post.board_id==1:
        abort(400)

    #block further yanks to the same board
    new_rel=PostRelationship(post_id=post.id,
                             board_id=post.board.id)
    db.add(new_rel)

    post.board_id=1
    
    db.add(post)
    db.commit()
    
    #clear board's listing caches
    cache.delete_memoized(Board.idlist, current_board)
    
    return "", 204

@app.route("/mod/take/<pid>", methods=["POST"])
@auth_required
@is_guildmaster
@validate_formkey
def mod_take_bid_pid(pid, board, v):

    post = get_post(pid)

    if not post.board_id==1:
        abort(422)

    if board.has_ban(post.author):
        abort(403)

    if not board.can_take(post):
        abort(403)

    post.board_id=board.id
    db.add(post)
    db.commit()

    #clear board's listing caches
    cache.delete_memoized(Board.idlist, board)
    
    return "", 204

@app.route("/mod/invite_mod/<bid>", methods=["POST"])
@auth_required
@is_guildmaster
@validate_formkey
def mod_invite_username(bid, board, v):

    username=request.form.get("username")
    user=get_user(username)

    if not board.can_invite_mod(user):
        abort(409)

    if not board.has_rescinded_invite(user):

        #notification

        text=f"You have been invited to join +{board.name} as a guildmaster. You can [click here]({board.permalink}/mod/mods) and accept this invitation. Or, if you weren't expecting this, you can ignore it."
        send_notification(user, text)

    new_mod=ModRelationship(user_id=user.id,
                            board_id=board.id,
                            accepted=False)
    db.add(new_mod)
    db.commit()
    return redirect(f"/+{board.name}/mod/mods")

@app.route("/mod/<bid>/rescind/<username>", methods=["POST"])
@auth_required
@is_guildmaster
@validate_formkey
def mod_rescind_bid_username(bid, username, board, v):
        
    user=get_user(username)

    invitation = db.query(ModRelationship).filter_by(board_id=board.id,
                                                     user_id=user.id,
                                                     accepted=False).first()
    if not invitation:
        abort(404)

    invitation.invite_rescinded=True

    db.add(invitation)
    db.commit()

    return "", 204
    

@app.route("/mod/accept/<bid>", methods=["POST"])
@auth_required
@validate_formkey
def mod_accept_board(bid, v):

    board=get_board(bid)

    x=board.has_invite(v)
    if not x:
        abort(404)

    x.accepted=True
    db.add(x)
    db.commit()
    return "", 204
    

@app.route("/mod/<bid>/remove/<username>", methods=["POST"])
@auth_required
@is_guildmaster
@validate_formkey
def mod_remove_username(bid, username, board, v):

    user=get_user(username)

    u_mod=board.has_mod(user)
    v_mod=board.has_mod(v)

    if not u_mod:
        abort(422)
    if v_mod.id > u_mod.id:
        abort(403)

    del v_mod
    db.delete(u_mod)
    db.commit()
    return "", 204

@app.route("/mod/is_banned/<bid>/<username>", methods=["GET"])
@auth_required
@is_guildmaster
@validate_formkey
def mod_is_banned_board_username(bid, username, board, v):

    user=get_user(username)

    result={"board":board.name,
            "user":user.username}

    if board.has_ban(user):
        result["is_banned"]=True
    else:
        result["is_banned"]=False

    return jsonify(result)


@app.route("/mod/<bid>/settings/over_18", methods=["POST"])
@auth_required
@is_guildmaster
@validate_formkey
def mod_bid_settings_nsfw(bid,  board, v):

    print(request.form)

    # nsfw
    board.over_18 = bool(request.form.get("over_18", False)=='true')

    db.add(board)
    db.commit()

    return "",204

@app.route("/mod/<bid>/settings/name", methods=["POST"])
@auth_required
@is_guildmaster
@validate_formkey
def mod_bid_settings_name(bid, board, v):
    # name capitalization
    new_name = request.form.get("guild_name", "").lstrip("+")

    if new_name.lower() == board.name.lower():
        board.name = new_name

    db.add(board)
    db.commit()

    return "", 204

@app.route("/mod/<bid>/settings/description", methods=["POST"])
@auth_required
@is_guildmaster
@validate_formkey
def mod_bid_settings_description(bid, board, v):
    #board description
    description = request.form.get("description")
    with CustomRenderer() as renderer:
        description_md=renderer.render(mistletoe.Document(description))
    description_html=sanitize(description_md, linkgen=True)


    board.description = description
    board.description_html=description_html

    db.add(board)
    db.commit()

    return "", 204

@app.route("/+<boardname>/mod/settings", methods=["GET"])
@auth_required
@is_guildmaster
def board_about_settings(boardname, board, v):

    return render_template("guild/settings.html", v=v, b=board)

@app.route("/+<boardname>/mod/mods", methods=["GET"])
@auth_desired
def board_about_mods(boardname, v):

    board=get_guild(boardname)

    me=board.has_mod(v)

    return render_template("guild/mods.html", v=v, b=board, me=me)


@app.route("/+<boardname>/mod/exiled", methods=["GET"])
@auth_required
@is_guildmaster
def board_about_exiled(boardname, board, v):

    username=request.args.get("user","")
    if username:
        users=db.query(User).filter_by(is_banned=0).filter(func.lower(User.username).contains(username.lower())).limit(25)
    else:
        users=[]
                                    

    return render_template("guild/bans.html", v=v, b=board, users=users)

@app.route("/api/subscribe/<boardname>", methods=["POST"])
@auth_required
def subscribe_board(boardname, v):

    board=get_guild(boardname)

    #check for existing subscription, canceled or otherwise
    sub= db.query(Subscription).filter_by(user_id=v.id, board_id=board.id).first()
    if sub:
        if sub.is_active:
            abort(409)
        else:
            #reactivate canceled sub
            sub.is_active=True
            db.add(sub)
            db.commit()
            return "", 204

    
    new_sub=Subscription(user_id=v.id,
                         board_id=board.id)

    db.add(new_sub)
    db.commit()

    #clear your cached guild listings
    cache.delete_memoized(User.idlist, v, kind="board")

    return "", 204


@app.route("/api/unsubscribe/<boardname>", methods=["POST"])
@auth_required
def unsubscribe_board(boardname, v):

    board=get_guild(boardname)

    #check for existing subscription
    sub= db.query(Subscription).filter_by(user_id=v.id, board_id=board.id).first()

    if not sub:
        abort(409)
    elif not sub.is_active:
        abort(409)

    sub.is_active=False

    db.add(sub)
    db.commit()

    #clear your cached guild listings
    cache.delete_memoized(User.idlist, v, kind="board")

    return "", 204

@app.route("/+<boardname>/mod/queue", methods=["GET"])
@auth_required
@is_guildmaster
def board_mod_queue(boardname, board, v):

    page=int(request.args.get("page",1))

    posts = board.submissions.filter_by(is_banned=False,
                                        mod_approved=0).filter(Submission.report_count>=1)

    if not v.over_18:
        posts=posts.filter_by(over_18=False)

    posts=posts.order_by(text('submissions.report_count desc')).offset((page-1)*25).limit(26)

    posts=[x for x in posts]

    next_exists=(len(posts)==26)

    posts=posts[0:25]

    return render_template("reported_posts.html",
                           listing=posts,
                           next_exists=next_exists,
                           page=page,
                           v=v,
                           b=board)
        
@app.route("/mod/queue", methods=["GET"])
@auth_required
def all_mod_queue(v):

    page=int(request.args.get("page",1))

    board_ids=[x.board_id for x in v.moderates.filter_by(accepted=True).all()]

    posts = db.query(Submission).filter(Submission.board_id.in_(board_ids),
                                        Submission.mod_approved==0,
                                        Submission.report_count >=1)

    if not v.over_18:
        posts=posts.filter_by(over_18=False)

    posts=posts.order_by(text('submissions.report_count desc')).offset((page-1)*25).limit(26)

    posts=[x for x in posts]

    next_exists=(len(posts)==26)

    posts=posts[0:25]

    return render_template("reported_posts.html",
                           listing=posts,
                           next_exists=next_exists,
                           page=page,
                           v=v)

@app.route("/mod/<bid>/images/profile", methods=["POST"])
@auth_required
@is_guildmaster
@validate_formkey
def mod_board_images_profile(bid, board, v):

    board.set_profile(request.files["profile"])

    return redirect(f"/+{board.name}/mod/settings?msg=Success#images")

@app.route("/mod/<bid>/images/banner", methods=["POST"])
@auth_required
@is_guildmaster
@validate_formkey
def mod_board_images_banner(bid, board, v):

    board.set_banner(request.files["banner"])
    return redirect(f"/+{board.name}/mod/settings?msg=Success#images")

@app.route("/mod/<bid>/delete/profile", methods=["POST"])
@auth_required
@is_guildmaster
@validate_formkey
def mod_board_images_delete_profile(bid, board, v):

    board.del_profile()

    return redirect(f"/+{board.name}/mod/settings?msg=Success#images")

@app.route("/mod/<bid>/delete/banner", methods=["POST"])
@auth_required
@is_guildmaster
@validate_formkey
def mod_board_images_delete_banner(bid, board, v):

    board.del_banner()

    return redirect(f"/+{board.name}/mod/settings?msg=Success#images")

    
@app.route("/+<boardname>/main.css", methods=["GET"])
@cache.memoize(3600*4)
def board_css(boardname):

    board=get_guild(boardname)


    with open("ruqqus/assets/style/board_main.scss", "r") as file:
        raw=file.read()

    #This doesn't use python's string formatting because
    #of some odd behavior with css files
    scss=raw.replace("{boardcolor}", board.color)
    
    resp=make_response(sass.compile(string=scss))
    resp.headers["Content-Type"]="text/css"

    return resp

@app.route("/+<boardname>/dark.css", methods=["GET"])
@cache.memoize(3600*4)
def board_dark_css(boardname):

    board=get_guild(boardname)


    with open("ruqqus/assets/style/board_dark.scss", "r") as file:
        raw=file.read()

    #This doesn't use python's string formatting because
    #of some odd behavior with css files
    scss=raw.replace("{boardcolor}", board.color)
    
    resp=make_response(sass.compile(string=scss))
    resp.headers["Content-Type"]="text/css"

    return resp

@app.route("/mod/<bid>/color", methods=["POST"])
@auth_required
@is_guildmaster
@validate_formkey
def mod_board_color(bid, board, v):

    color=str(request.form.get("color",""))

    if len(color) !=6:
        color="603abb"

    r=color[0:1]
    g=color[2:3]
    b=color[4:5]

    try:
        if any([int(x,16)>255 for x in [r,g,b]]):
            color="603abb"
    except ValueError:
        color="603abb"

    board.color=color
    db.add(board)
    db.commit()

    cache.delete_memoized(board_css, boardname=board.name)
    cache.delete_memoized(board_dark_css, boardname=board.name)

    return redirect(f"/+{board.name}/mod/settings?msg=Success#color")
