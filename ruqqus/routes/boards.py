from urllib.parse import urlparse
import mistletoe
import re
import sass
import threading
import time
import os.path

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.markdown import *
from ruqqus.helpers.get import *
from ruqqus.helpers.alerts import *
from ruqqus.helpers.session import *
from ruqqus.helpers.aws import check_csam_url
from ruqqus.classes import *
from .front import guild_ids
from ruqqus.classes.rules import *
from ruqqus.classes.categories import CATEGORIES
from flask import *

from ruqqus.__main__ import app, limiter, cache

valid_board_regex = re.compile("^[a-zA-Z0-9][a-zA-Z0-9_]{2,24}$")


@app.route("/create_guild", methods=["GET"])
@is_not_banned
@no_negative_balance("html")
def create_board_get(v):
    if not v.can_make_guild:
        return render_template("message.html",
                               v=v,
                               title="You already lead 10 guilds." if not v.can_join_gms else "Unable to make a guild. For now.",
                               message="You need to step down from a guild before you can make any more." if not v.can_join_gms else "You need more Reputation.")

    # check # recent boards made by user
    cutoff = int(time.time()) - 60 * 60 * 24
    recent = g.db.query(Board).filter(
        Board.creator_id == v.id,
        Board.created_utc >= cutoff).all()
    if len([x for x in recent]) >= 2:
        return render_template("message.html",
                               v=v,
                               title="You need to wait a bit.",
                               message="You can only create up to 2 guilds per day. Try again later."
                               ), 429

    return render_template(
        "make_board.html", 
        v=v,
        categories=CATEGORIES
        )


@app.route("/api/board_available/<name>", methods=["GET"])
@app.route("/api/v1/board_available/<name>", methods=["GET"])
@auth_desired
@api()
def api_board_available(name, v):
    if get_guild(name, graceful=True) or not re.match(valid_board_regex, name):
        return jsonify({"board": name, "available": False})
    else:
        return jsonify({"board": name, "available": True})


@app.route("/create_guild", methods=["POST"])
@is_not_banned
@no_negative_balance("html")
@validate_formkey
def create_board_post(v):
    if not v.can_make_guild:
        return render_template("make_board.html",
                               title="Unable to make board",
                               error="You need more Reputation before you can make a Guild."
                               )

    board_name = request.form.get("name")
    board_name = board_name.lstrip("+")
    description = request.form.get("description")

    if not re.match(valid_board_regex, board_name):
        return render_template("make_board.html",
                               v=v,
                               error="Guild names must be 3-25 letters or numbers.",
                               description=description
                               )

    # check name
    if get_guild(board_name, graceful=True):
        return render_template("make_board.html",
                               v=v,
                               error="That Guild already exists.",
                               description=description
                               )

    # check # recent boards made by user
    cutoff = int(time.time()) - 60 * 60 * 24
    alt_ids=[x.id for x in v.alts]
    user_ids=[v.id]+alt_ids
    recent = g.db.query(Board).filter(
        Board.creator_id.in_(user_ids),
        Board.created_utc >= cutoff).all()
    if len([x for x in recent]) >= 2:
        return render_template("message.html",
                               title="You need to wait a bit.",
                               message="You can only create up to 2 guilds per day. Try again later."
                               ), 429

    subcat=int(request.form.get("category",0))
    subcat=g.db.query(SubCategory).filter_by(id=subcat).first()
    if not subcat:
        return render_template("message.html",
                               title="Category required.",
                               message="You need to select a category."
                               ), 400


    with CustomRenderer() as renderer:
        description_md = renderer.render(mistletoe.Document(description))
    description_html = sanitize(description_md, linkgen=True)

    # make the board

    new_board = Board(name=board_name,
                      description=description,
                      description_html=description_html,
                      over_18=bool(request.form.get("over_18", "")),
                      creator_id=v.id,
                      subcat_id=subcat.id
                      )

    g.db.add(new_board)

    g.db.commit()

    # add user as mod
    mod = ModRelationship(user_id=v.id,
                          board_id=new_board.id,
                          accepted=True,
                          perm_full=True,
                          perm_access=True,
                          perm_content=True,
                          perm_appearance=True,
                          perm_config=True)
    g.db.add(mod)

    # add subscription for user
    sub = Subscription(user_id=v.id,
                       board_id=new_board.id)
    g.db.add(sub)

    #add guild creation mod log entry
    ma = ModAction(
        user_id=v.id,
        board_id=new_board.id,
        kind="create_guild",
        )
    g.db.add(ma)

    # clear cache
    cache.delete_memoized(guild_ids, sort="new")

    return redirect(new_board.permalink)


@app.route("/r/<name>")
def reddit_moment_redirect(name):
    return redirect(f"/+{name}")


@app.route("/+<name>", methods=["GET"])
@app.route("/api/v1/guild/<name>/listing", methods=["GET"])
@auth_desired
@api("read")
def board_name(name, v):

    board = get_guild(name)

    if not board.name == name and not request.path.startswith('/api/v1'):
        return redirect(request.path.replace(name, board.name))

    if board.is_banned and not (v and v.admin_level >= 3):
        return {'html': lambda: (render_template("board_banned.html",
                                                 v=v,
                                                 b=board,
                                                 p=True
                                                 ), 410),
                'api': lambda: (jsonify({'error': f'410 Gone - +{board.name} is banned.'}), 410)
                }
    if board.over_18 and not (v and v.over_18) and not session_over18(board):
        t = int(time.time())
        return {'html': lambda: render_template("errors/nsfw.html",
                                                v=v,
                                                t=t,
                                                lo_formkey=make_logged_out_formkey(
                                                    t),
                                                board=board
                                                ),
                'api': lambda: jsonify({'error': f'+{board.name} is NSFW.'})
                }

    sort = request.args.get("sort", "hot")
    page = int(request.args.get("page", 1))
    t = request.args.get("t", "all")
    ignore_pinned = bool(request.args.get("ignore_pinned", False))

    ids = board.idlist(sort=sort,
                       t=t,
                       page=page,
                       nsfw=(v and v.over_18) or session_over18(board),
                       v=v,
                       gt=int(request.args.get("utc_greater_than", 0)),
                       lt=int(request.args.get("utc_less_than", 0))
                       )

    next_exists = (len(ids) == 26)
    ids = ids[0:25]

    if page == 1 and sort != "new" and not ignore_pinned:
        stickies = g.db.query(Submission.id).filter_by(board_id=board.id,
                                                       is_banned=False,
                                                       is_deleted=False,
                                                       is_pinned=True).order_by(Submission.id.asc()
                                                                                ).limit(4)
        stickies = [x[0] for x in stickies]
        ids = stickies + ids

    posts = get_posts(ids,
                      sort=sort,
                      v=v)

    return {'html': lambda: render_template("board.html",
                                            b=board,
                                            v=v,
                                            time_filter=t,
                                            listing=posts,
                                            next_exists=next_exists,
                                            sort_method=sort,
                                            page=page,
                                            is_subscribed=(v and board.has_subscriber(v)
                                                           )
                                            ),
            'api': lambda: jsonify({"data": [x.json for x in posts],
                                    "next_exists": next_exists
                                    }
                                   )
            }

@app.route("/mod/distinguish_post/<bid>/<pid>", methods=["POST"])
@app.route("/api/v1/distinguish_post/<bid>/<pid>", methods=["POST"])
@auth_required
@is_guildmaster("content")
@api("guildmaster")
def mod_distinguish_post(bid, pid, board, v):

    #print(pid, board, v)

    post = get_post(pid, v=v)

    if not post.board_id==board.id:
        abort(400)

    if post.author_id != v.id:
        abort(403)

    if post.gm_distinguish:
        post.gm_distinguish = 0
    else:
        post.gm_distinguish = board.id
    g.db.add(post)

    ma=ModAction(
        kind="herald_post" if post.gm_distinguish else "unherald_post",
        user_id=v.id,
        target_submission_id=post.id,
        board_id=board.id
        )
    g.db.add(ma)

    return "", 204

@app.route("/mod/distinguish_comment/<bid>/<cid>", methods=["POST"])
@app.route("/api/v1/distinguish_comment/<bid>/<cid>", methods=["POST"])
@auth_required
@is_guildmaster('content')
@api("guildmaster")
def mod_distinguish_comment(bid, cid, board, v):

    comment = get_comment(cid, v=v)

    if not comment.post.board_id==board.id:
        abort(400)

    if comment.author_id != v.id:
        abort(403)

    if comment.gm_distinguish:
        comment.gm_distinguish = 0
    else:
        comment.gm_distinguish = board.id

    g.db.add(comment)

    ma=ModAction(
        kind="herald_comment" if comment.gm_distinguish else "unherald_comment",
        user_id=v.id,
        target_comment_id=comment.id,
        board_id=board.id
        )
    g.db.add(ma)

    return "", 204

@app.route("/mod/kick/<bid>/<pid>", methods=["POST"])
@app.route("/api/v1/kick/<bid>/<pid>", methods=["POST"])
@auth_required
@is_guildmaster('content')
@api("guildmaster")
@validate_formkey
def mod_kick_bid_pid(bid, pid, board, v):

    post = get_post(pid)

    if not post.board_id == board.id:
        abort(400)

    post.board_id = 1
    post.guild_name = "general"
    post.is_pinned = False
    g.db.add(post)

    cache.delete_memoized(Board.idlist, board)

    ma=ModAction(
        kind="kick_post",
        user_id=v.id,
        target_submission_id=post.id,
        board_id=board.id
        )
    g.db.add(ma)

    return "", 204


@app.route("/mod/accept/<bid>/<pid>", methods=["POST"])
@app.route("/api/v1/accept/<bid>/<pid>", methods=["POST"])
@auth_required
@is_guildmaster('content')
@api("guildmaster")
@validate_formkey
def mod_accept_bid_pid(bid, pid, board, v):

    post = get_post(pid)
    if not post.board_id == board.id:
        abort(400)

    if post.mod_approved:
        return ({"error":"Already approved"})

    post.mod_approved = v.id
    g.db.add(post)

    ma=ModAction(
        kind="approve_post",
        user_id=v.id,
        target_submission_id=post.id,
        board_id=board.id
        )
    g.db.add(ma)

    return "", 204


@app.route("/mod/exile/<bid>", methods=["POST"])
@app.route("/api/v1/exile/<bid>", methods=["POST"])
@auth_required
@is_guildmaster('access')
@api("guildmaster")
@validate_formkey
def mod_ban_bid_user(bid, board, v):

    user = get_user(request.values.get("username"), graceful=True)

    #check for post/comment
    item = request.values.get("thing")
    if item:
        item=get_from_fullname(item)

    if not user:
        return jsonify({"error": "That user doesn't exist."}), 404

    if user.id == v.id:
        return jsonify({"error": "You can't exile yourself."}), 409

    if g.db.query(BanRelationship).filter_by(user_id=user.id, board_id=board.id, is_active=True).first():
        return jsonify({"error": f"@{user.username} is already exiled from +{board.name}."}), 409

    if board.has_contributor(user):
        return jsonify({"error": f"@{user.username} is an approved contributor to +{board.name} and can't currently be exiled."}), 409

    if board.has_mod(user):
        return jsonify({"error": "You can't exile other guildmasters."}), 409

    # you can only exile a user who has previously participated in the guild
    if not board.has_participant(user):
        return jsonify({"error": f"@{user.username} hasn't participated in +{board.name}."}), 403

    # check for an existing deactivated ban
    existing_ban = g.db.query(BanRelationship).filter_by(
        user_id=user.id, board_id=board.id, is_active=False).first()
    if existing_ban:
        existing_ban.is_active = True
        existing_ban.created_utc = int(time.time())
        existing_ban.banning_mod_id = v.id
        g.db.add(existing_ban)
    else:
        new_ban = BanRelationship(user_id=user.id,
                                  board_id=board.id,
                                  banning_mod_id=v.id,
                                  is_active=True)
        g.db.add(new_ban)

        text = f"You have been exiled from +{board.name}.\n\nNone of your existing posts or comments have been removed, however, you will not be able to make any new posts or comments in +{board.name}."
        if item:
            text+= "\n\nYou were exiled for [this "
            text+= "comment" if isinstance(item, Comment) else "post"
            text+= f"]({item.permalink})."

        send_notification(user, text)

    if item:
        if isinstance(item, Submission):
            note=f'for <a href="{item.permalink}">post</a>'
        elif isinstance(item, Comment):
            note=f'for <a href="{item.permalink}">comment</a>'
        else:
            note=None
    else:
        note=None

    ma=ModAction(
        kind="exile_user",
        user_id=v.id,
        target_user_id=user.id,
        board_id=board.id,
        note=note
        )
    g.db.add(ma)


    if request.args.get("toast"):
        return jsonify({"message": f"@{user.username} was exiled from +{board.name}"})
    else:
        return "", 204


@app.route("/mod/unexile/<bid>", methods=["POST"])
@app.route("/api/v1/unexile/<bid>", methods=["POST"])
@auth_required
@is_guildmaster('access')
@api("guildmaster")
@validate_formkey
def mod_unban_bid_user(bid, board, v):

    user = get_user(request.values.get("username"))

    x =  g.db.query(BanRelationship).filter_by(board_id=board.id, user_id=user.id, is_active=True).first()

    if not x:
        abort(409)

    x.is_active = False

    g.db.add(x)

    ma=ModAction(
        kind="unexile_user",
        user_id=v.id,
        target_user_id=user.id,
        board_id=board.id
        )
    g.db.add(ma)

    return "", 204


@app.route("/user/kick/<pid>", methods=["POST"])
@auth_required
@validate_formkey
def user_kick_pid(pid, v):

    # allows a user to yank their content back to +general if it was there
    # previously

    post = get_post(pid)

    current_board = post.board

    if not post.author_id == v.id:
        abort(403)

    if post.board_id == post.original_board_id:
        abort(403)

    if post.board_id == 1:
        abort(400)

    # block further yanks to the same board
    new_rel = PostRelationship(post_id=post.id,
                               board_id=post.board.id)
    g.db.add(new_rel)

    post.board_id = 1
    post.is_pinned = False

    g.db.add(post)

    g.db.commit()

    # clear board's listing caches
    cache.delete_memoized(Board.idlist, current_board)

    return "", 204


@app.route("/mod/take/<pid>", methods=["POST"])
@app.route("/api/v1/mod/take/<pid>")
@auth_required
@is_guildmaster("content")
@validate_formkey
@api("guildmaster")
def mod_take_pid(pid, board, v):

    bid = request.form.get("board_id", request.form.get("guild", None))
    if not bid:
        abort(400)

    post = get_post(pid, graceful=True)
    if not post:
        return jsonify({"error": "invalid post id"}), 404

    #check cooldowns
    now=int(time.time())
    if post.original_board_id != board.id and post.author_id != v.id:
        if now <  v.last_yank_utc + 3600:
            return jsonify({'error':f"You've yanked a post recently. You need to wait 1 hour between yanks."}), 401
        elif now <  board.last_yank_utc + 3600:
            return jsonify({'error':f"+{board.name} has yanked a post recently. The Guild needs to wait 1 hour between yanks."}), 401


    if board.is_banned:
        return jsonify({'error': f"+{board.name} is banned. You can't yank anything there."}), 403

    if not post.board_id == 1:
        return jsonify({'error': f"This post is no longer in +general"}), 403

    if not board.has_mod(v):
        return jsonify({'error': f"You are no longer a guildmaster of +{board.name}"}), 403

    if board.has_ban(post.author):
        return jsonify({'error': f"@{post.author.username} is exiled from +{board.name}, so you can't yank their post there."}), 403

    if post.author.any_block_exists(v):
        return jsonify({'error': f"You can't yank @{post.author.username}'s content."}), 403

    if not board.can_take(post):
        return jsonify({'error': f"You can't yank this particular post to +{board.name}."}), 403

    if board.is_private and post.original_board_id != board.id:
        return jsonify({'error': f"+{board.name} is private, so you can only yank content that started there."}), 403

    post.board_id = board.id
    post.guild_name = board.name
    g.db.add(post)

    if post.original_board_id != board.id and post.author_id != v.id:
        board.last_yank_utc=now
        v.last_yank_utc=now

        g.db.add(board)
        g.db.add(v)

        notif_text=f"Your post [{post.title}]({post.permalink}) has been Yanked from +general to +{board.name}.\n\nIf you don't want it there, just click `Remove from +{board.name}` on the post."
        send_notification(post.author, notif_text)
        g.db.commit()

    # clear board's listing caches
    cache.delete_memoized(Board.idlist, board)

    ma=ModAction(
        kind="yank_post",
        user_id=v.id,
        target_submission_id=post.id,
        board_id=board.id
        )
    g.db.add(ma)

    return "", 204


@app.route("/mod/invite_mod/<bid>", methods=["POST"])
@auth_required
@is_guildmaster("full")
@validate_formkey
def mod_invite_username(bid, board, v):

    username = request.form.get("username", '').lstrip('@')
    user = get_user(username)

    if not user.can_join_gms:
        return jsonify({"error": f"@{user.username} already leads enough guilds."}), 409

    x = g.db.query(ModRelationship).filter_by(
        user_id=user.id, board_id=board.id).first()

    if x and x.accepted:
        return jsonify({"error": f"@{user.username} is already a mod."}), 409

    if x and not x.invite_rescinded:
        return jsonify({"error": f"@{user.username} has already been invited."}), 409

    if x:

        x.invite_rescinded = False
        g.db.add(x)

    else:
        x = ModRelationship(
            user_id=user.id,
            board_id=board.id,
            accepted=False,
            perm_full=True,
            perm_content=True,
            perm_appearance=True,
            perm_access=True,
            perm_config=True
            )

        text = f"You have been invited to join +{board.name} as a guildmaster. You can [click here]({board.permalink}/mod/mods) and accept this invitation. Or, if you weren't expecting this, you can ignore it."
        send_notification(user, text)

        g.db.add(x)

    ma=ModAction(
        kind="invite_mod",
        user_id=v.id,
        target_user_id=user.id,
        board_id=board.id,
        note=x.permchangelist
        )
    g.db.add(ma)

    return "", 204


@app.route("/mod/<bid>/rescind/<username>", methods=["POST"])
@auth_required
@is_guildmaster("full")
@validate_formkey
def mod_rescind_bid_username(bid, username, board, v):

    user = get_user(username)

    invitation = g.db.query(ModRelationship).filter_by(board_id=board.id,
                                                       user_id=user.id,
                                                       accepted=False).first()
    if not invitation:
        abort(404)

    invitation.invite_rescinded = True

    g.db.add(invitation)
    ma=ModAction(
        kind="uninvite_mod",
        user_id=v.id,
        target_user_id=user.id,
        board_id=board.id
        )
    g.db.add(ma)
    return "", 204


@app.route("/mod/accept/<bid>", methods=["POST"])
@auth_required
@validate_formkey
def mod_accept_board(bid, v):

    board = get_board(bid)

    x = board.has_invite(v)
    if not x:
        abort(404)

    if not v.can_join_gms:
        return jsonify({"error": f"You already lead enough guilds."}), 409

    x.accepted = True
    g.db.add(x)

    ma=ModAction(
        kind="accept_mod_invite",
        user_id=v.id,
        target_user_id=v.id,
        board_id=board.id
        )
    g.db.add(ma)

    return "", 204

@app.route("/mod/<bid>/step_down", methods=["POST"])
@auth_required
@is_guildmaster()
@validate_formkey
def mod_step_down(bid, board, v):


    v_mod = board.has_mod(v)

    if not v_mod:
        abort(404)

    g.db.delete(v_mod)

    ma=ModAction(
        kind="dethrone_self",
        user_id=v.id,
        target_user_id=v.id,
        board_id=board.id
        )
    g.db.add(ma) 
    return "", 204



@app.route("/mod/<bid>/remove/<username>", methods=["POST"])
@auth_required
@is_guildmaster("full")
@validate_formkey
def mod_remove_username(bid, username, board, v):

    user = get_user(username)

    u_mod = board.has_mod(user)
    v_mod = board.has_mod(v)

    if not u_mod:
        abort(400)
    elif not v_mod:
        abort(400)

    if not u_mod.board_id==board.id:
        abort(400)

    if not v_mod.board_id==board.id:
        abort(400)

    if v_mod.id > u_mod.id:
        abort(403)

    g.db.delete(u_mod)

    ma=ModAction(
        kind="remove_mod",
        user_id=v.id,
        target_user_id=user.id,
        board_id=board.id
        )
    g.db.add(ma)

    return "", 204


@app.route("/mod/is_banned/<bid>/<username>", methods=["GET"])
@auth_required
@is_guildmaster("access")
@validate_formkey
def mod_is_banned_board_username(bid, username, board, v):

    user = get_user(username)

    result = {"board": board.name,
              "user": user.username}

    if board.has_ban(user):
        result["is_banned"] = True
    else:
        result["is_banned"] = False

    return jsonify(result)


@app.route("/mod/<bid>/settings/over_18", methods=["POST"])
@auth_required
@is_guildmaster("config")
@validate_formkey
def mod_bid_settings_nsfw(bid, board, v):

    # nsfw
    board.over_18 = bool(request.form.get("over_18", False) == 'true')

    g.db.add(board)

    ma=ModAction(
        kind="update_settings",
        user_id=v.id,
        board_id=board.id,
        note=f"over_18={board.over_18}"
        )
    g.db.add(ma)
    return "", 204


@app.route("/mod/<bid>/settings/opt_out", methods=["POST"])
@auth_required
@is_guildmaster("config")
@validate_formkey
def mod_bid_settings_optout(bid, board, v):

    # nsfw
    board.all_opt_out = bool(request.form.get("opt_out", False) == 'true')

    g.db.add(board)

    ma=ModAction(
        kind="update_settings",
        user_id=v.id,
        board_id=board.id,
        note=f"all_opt_out={board.all_opt_out}"
        )
    g.db.add(ma)
    return "", 204


@app.route("/mod/<bid>/settings/restricted", methods=["POST"])
@auth_required
@is_guildmaster("config")
@validate_formkey
def mod_bid_settings_restricted(bid, board, v):

    # toggle restricted setting
    board.restricted_posting = bool(
        request.form.get(
            "restrictswitch",
            False) == 'true')

    g.db.add(board)

    ma=ModAction(
        kind="update_settings",
        user_id=v.id,
        board_id=board.id,
        note=f"restricted={board.restricted_posting}"
        )
    g.db.add(ma)
    return "", 204


@app.route("/mod/<bid>/settings/private", methods=["POST"])
@auth_required
@is_guildmaster("config")
@validate_formkey
def mod_bid_settings_private(bid, board, v):

    # toggle privacy setting
    board.is_private = bool(request.form.get("guildprivacy", False) == 'true')

    g.db.add(board)

    ma=ModAction(
        kind="update_settings",
        user_id=v.id,
        board_id=board.id,
        note=f"private={board.is_private}"
        )
    g.db.add(ma)
    return "", 204


@app.route("/mod/<bid>/settings/name", methods=["POST"])
@auth_required
@is_guildmaster("config")
@validate_formkey
def mod_bid_settings_name(bid, board, v):
    # name capitalization
    new_name = request.form.get("guild_name", "").lstrip("+")

    if new_name.lower() == board.name.lower():
        board.name = new_name
        g.db.add(board)


        ma=ModAction(
            kind="update_settings",
            user_id=v.id,
            board_id=board.id,
            note=f"name={board.name}"
            )
        g.db.add(ma)
        return "", 204
    else:
        return "", 422


@app.route("/mod/<bid>/settings/description", methods=["POST"])
@auth_required
@is_guildmaster("config")
@validate_formkey
def mod_bid_settings_description(bid, board, v):
    # board description
    description = request.form.get("description")
    with CustomRenderer() as renderer:
        description_md = renderer.render(mistletoe.Document(description))
    description_html = sanitize(description_md, linkgen=True)

    board.description = description
    board.description_html = description_html

    g.db.add(board)

    ma=ModAction(
        kind="update_settings",
        user_id=v.id,
        board_id=board.id,
        note=f"update description"
        )
    g.db.add(ma)
    return "", 204


@app.route("/mod/<bid>/settings/banner", methods=["POST"])
@auth_required
@is_guildmaster("appearance")
@validate_formkey
def mod_settings_toggle_banner(bid, board, v):
    # toggle show/hide banner
    board.hide_banner_data = bool(
        request.form.get(
            "hidebanner",
            False) == 'true')

    g.db.add(board)
    return "", 204


@app.route("/mod/<bid>/settings/add_rule", methods=["POST"])
@auth_required
@is_guildmaster("full")
@validate_formkey
def mod_add_rule(bid, board, v):
    # board description
    rule = request.form.get("rule1")
    rule2 = request.form.get("rule2")
    if not rule2:
        with CustomRenderer() as renderer:
            rule_md = renderer.render(mistletoe.Document(rule))
        rule_html = sanitize(rule_md, linkgen=True)

        new_rule = Rules(board_id=bid, rule_body=rule, rule_html=rule_html)
        g.db.add(new_rule)

    else:
        """
        im guessing here we should
        do a loop for
        adding multiple rules
        """
        pass

    return "", 204


@app.route("/mod/<bid>/settings/edit_rule", methods=["POST"])
@auth_required
@is_guildmaster("full")
@validate_formkey
def mod_edit_rule(bid, board, v):
    r = base36decode(request.form.get("rid"))
    r = g.db.query(Rules).filter_by(id=r)

    if not r:
        abort(500)

    if board.is_banned:
        abort(403)

    if board.has_ban(v):
        abort(403)

    body = request.form.get("body", "")
    with CustomRenderer() as renderer:
        body_md = renderer.render(mistletoe.Document(body))
    body_html = sanitize(body_md, linkgen=True)

    r.rule_body = body
    r.rule_html = body_html
    r.edited_utc = int(time.time())

    g.db.add(r)

    return "", 204


@app.route("/+<boardname>/mod/settings", methods=["GET"])
@auth_required
@is_guildmaster("config")
def board_about_settings(boardname, board, v):

    return render_template(
        "guild/settings.html",
        v=v,
        b=board,
        categories=CATEGORIES
        )


@app.route("/+<boardname>/mod/appearance", methods=["GET"])
@auth_required
@is_guildmaster("appearance")
def board_about_appearance(boardname, board, v):

    return render_template("guild/appearance.html", v=v, b=board)


@app.route("/+<boardname>/mod/mods", methods=["GET"])
@app.route("/api/v1/<boardname>/mod/mods", methods=["GET"])
@auth_desired
@api("read")
def board_about_mods(boardname, v):

    board = get_guild(boardname)

    me = board.has_mod(v)

    return {
        "html":lambda:render_template("guild/mods.html", v=v, b=board, me=me),
        "api":lambda:jsonify({"data":[x.json for x in board.mods_list]})
        }


@app.route("/+<boardname>/mod/exiled", methods=["GET"])
@app.route("/api/v1/<boardname>/mod/exiled", methods=["GET"])
@auth_required
@is_guildmaster("access")
@api("read", "guildmaster")
def board_about_exiled(boardname, board, v):

    page = int(request.args.get("page", 1))

    bans = board.bans.filter_by(is_active=True).order_by(
        BanRelationship.created_utc.desc()).offset(25 * (page - 1)).limit(26)

    bans = [ban for ban in bans]
    next_exists = (len(bans) == 26)
    bans = bans[0:25]

    return {
        "html":lambda:render_template(
            "guild/bans.html", 
            v=v, 
            b=board, 
            bans=bans,
            page=page,
            next_exists=next_exists
            ),
        "api":lambda:jsonify({"data":[x.json for x in bans]})
        }


@app.route("/+<boardname>/mod/contributors", methods=["GET"])
@auth_required
@is_guildmaster("access")
def board_about_contributors(boardname, board, v):

    page = int(request.args.get("page", 1))

    contributors = board.contributors.filter_by(is_active=True).order_by(
        ContributorRelationship.created_utc.desc()).offset(25 * (page - 1)).limit(26)

    contributors = [x for x in contributors]
    next_exists = (len(contributors) == 26)
    contributors = contributors[0:25]

    return render_template(
        "guild/contributors.html", 
        v=v,
        b=board, 
        contributors=contributors,
        page=page,
        next_exists=next_exists
        )


@app.route("/api/subscribe/<boardname>", methods=["POST"])
@auth_required
def subscribe_board(boardname, v):

    board = get_guild(boardname)

    # check for existing subscription, canceled or otherwise
    sub = g.db.query(Subscription).filter_by(
        user_id=v.id, board_id=board.id).first()
    if sub:
        if sub.is_active:
            return jsonify({"error": f"You are already a member of +{board.name}"}), 409
        else:
            # reactivate canceled sub
            sub.is_active = True
            g.db.add(sub)

    else:

        new_sub = Subscription(user_id=v.id,
                               board_id=board.id)

        g.db.add(new_sub)

    g.db.flush()

    # clear your cached guild listings
    cache.delete_memoized(User.idlist, v, kind="board")

    # update board trending rank
    board.rank_trending = board.trending_rank
    board.stored_subscriber_count = board.subscriber_count
    g.db.add(board)

    return jsonify({"message": f"Joined +{board.name}"}), 200


@app.route("/api/unsubscribe/<boardname>", methods=["POST"])
@auth_required
def unsubscribe_board(boardname, v):

    board = get_guild(boardname)

    # check for existing subscription
    sub = g.db.query(Subscription).filter_by(
        user_id=v.id, board_id=board.id).first()

    if not sub or not sub.is_active:
        return jsonify({"error": f"You aren't a member of +{board.name}"}), 409

    sub.is_active = False

    g.db.add(sub)
    g.db.flush()

    # clear your cached guild listings
    cache.delete_memoized(User.idlist, v, kind="board")

    board.rank_trending = board.trending_rank
    board.stored_subscriber_count = board.subscriber_count
    g.db.add(board)

    return jsonify({"message": f"Left +{board.name}"}), 200


@app.route("/+<boardname>/mod/queue", methods=["GET"])
@auth_required
@is_guildmaster("content")
def board_mod_queue(boardname, board, v):

    page = int(request.args.get("page", 1))

    ids = g.db.query(Submission.id).filter_by(board_id=board.id,
                                              is_banned=False,
                                              mod_approved=None
                                              ).join(Report, Report.post_id == Submission.id)

    if not v.over_18:
        ids = ids.filter(Submission.over_18 == False)

    ids = ids.order_by(Submission.id.desc()).offset((page - 1) * 25).limit(26)

    ids = [x[0] for x in ids]

    next_exists = (len(ids) == 26)

    ids = ids[0:25]

    posts = get_posts(ids, v=v)

    return render_template("guild/reported_posts.html",
                           listing=posts,
                           next_exists=next_exists,
                           page=page,
                           v=v,
                           b=board)


@app.route("/mod/queue", methods=["GET"])
@auth_required
def all_mod_queue(v):

    page = int(request.args.get("page", 1))

    board_ids = [
        x.id for x in v.boards_modded]

    ids = g.db.query(Submission.id).options(lazyload('*')).filter(Submission.board_id.in_(board_ids),
                                                                  Submission.mod_approved is None,
                                                                  Submission.is_banned == False
                                                                  ).join(Report, Report.post_id == Submission.id)

    if not v.over_18:
        ids = ids.filter(Submission.over_18 == False)

    ids = ids.order_by(Submission.id.desc()).offset((page - 1) * 25).limit(26)

    ids = [x for x in ids]

    next_exists = (len(ids) == 26)

    ids = ids[0:25]

    posts = get_posts(ids, v=v)

    return render_template("guild/reported_posts.html",
                           listing=posts,
                           next_exists=next_exists,
                           page=page,
                           v=v,
                           b=None)


@app.route("/mod/<bid>/images/profile", methods=["POST"])
@auth_required
@is_guildmaster("appearance")
@validate_formkey
def mod_board_images_profile(bid, board, v):

    board.set_profile(request.files["profile"])

    # anti csam
    new_thread = threading.Thread(target=check_csam_url,
                                  args=(board.profile_url,
                                        v,
                                        lambda: board.del_profile()
                                        )
                                  )
    new_thread.start()

    ma=ModAction(
        kind="update_appearance",
        user_id=v.id,
        board_id=board.id,
        note=f"uploaded profile image"
        )
    g.db.add(ma)

    return redirect(f"/+{board.name}/mod/appearance?msg=Success#images")


@app.route("/mod/<bid>/images/banner", methods=["POST"])
@auth_required
@is_guildmaster("appearance")
@validate_formkey
def mod_board_images_banner(bid, board, v):

    board.set_banner(request.files["banner"])

    # anti csam
    new_thread = threading.Thread(target=check_csam_url,
                                  args=(board.banner_url,
                                        v,
                                        lambda: board.del_banner()
                                        )
                                  )
    new_thread.start()

    ma=ModAction(
        kind="update_appearance",
        user_id=v.id,
        board_id=board.id,
        note=f"uploaded banner image"
        )
    g.db.add(ma)

    return redirect(f"/+{board.name}/mod/appearance?msg=Success#images")


@app.route("/mod/<bid>/delete/profile", methods=["POST"])
@auth_required
@is_guildmaster("appearance")
@validate_formkey
def mod_board_images_delete_profile(bid, board, v):

    board.del_profile()

    ma=ModAction(
        kind="update_appearance",
        user_id=v.id,
        board_id=board.id,
        note=f"removed profile image"
        )
    g.db.add(ma)

    return redirect(f"/+{board.name}/mod/appearance?msg=Success#images")


@app.route("/mod/<bid>/delete/banner", methods=["POST"])
@auth_required
@is_guildmaster("appearance")
@validate_formkey
def mod_board_images_delete_banner(bid, board, v):

    board.del_banner()

    ma=ModAction(
        kind="update_appearance",
        user_id=v.id,
        board_id=board.id,
        note=f"removed banner image"
        )
    g.db.add(ma)

    return redirect(f"/+{board.name}/mod/appearance?msg=Success#images")


@app.route("/assets/<boardname>/main/<x>.css", methods=["GET"])
#@cache.memoize(60*6*24)
def board_css(boardname, x):

    # temp

    board = get_guild(boardname)

    if int(x) != board.color_nonce:
        return redirect(board.css_url)

    try:
        with open(os.path.join(os.path.expanduser('~'), "ruqqus/ruqqus/assets/style/board_main.scss"), "r") as file:
            raw = file.read()
    except FileNotFoundError:
        return redirect("/assets/style/main.css")

    # This doesn't use python's string formatting because
    # of some odd behavior with css files
    scss = raw.replace("{boardcolor}", board.color)

    try:
        resp = Response(sass.compile(string=scss), mimetype='text/css')
    except sass.CompileError:
        return redirect("/assets/style/main.css")

    resp.headers.add("Cache-Control", "public")

    return resp


@app.route("/assets/<boardname>/dark/<x>.css", methods=["GET"])
#@cache.memoize(60*60*24)
def board_dark_css(boardname, x):

    # temp
    # return redirect("/assets/style/main_dark.css")

    board = get_guild(boardname)

    if int(x) != board.color_nonce:
        return redirect(board.css_dark_url)

    try:
        with open(os.path.join(os.path.expanduser('~'), "ruqqus/ruqqus/assets/style/board_dark.scss"), "r") as file:
            raw = file.read()
    except FileNotFoundError:
        return redirect("/assets/style/main_dark.css")

    # This doesn't use python's string formatting because
    # of some odd behavior with css files
    scss = raw.replace("{boardcolor}", board.color)

    try:
        resp = Response(sass.compile(string=scss), mimetype='text/css')
    except sass.CompileError:
        return redirect("/assets/style/main_dark.css")

    resp.headers.add("Cache-Control", "public")
    return resp


@app.route("/mod/<bid>/color", methods=["POST"])
@auth_required
@is_guildmaster("appearance")
@validate_formkey
def mod_board_color(bid, board, v):

    color = str(request.form.get("color", "")).strip()

    # Remove the '#' from the beginning in case it was entered.
    if color.startswith('#'):
        color = color[1:]

    if len(color) != 6:
        return render_template("guild/appearance.html",
                               v=v, b=board, error="Invalid color code."), 400

    red = color[0:1]
    green = color[2:3]
    blue = color[4:5]

    try:
        if any([int(x, 16) > 255 for x in [red, green, blue]]):
            return render_template(
                "guild/appearance.html", v=v, b=board, error="Invalid color code."), 400
    except ValueError:
        return render_template("guild/appearance.html",
                               v=v, b=board, error="Invalid color code."), 400

    board.color = color
    board.color_nonce += 1

    g.db.add(board)

    try:
        cache.delete_memoized(board_css, board.name)
        cache.delete_memoized(board_dark_css, board.name)
    except BaseException:
        pass

    ma=ModAction(
        kind="update_appearance",
        user_id=v.id,
        board_id=board.id,
        note=f"color=#{board.color}"
        )
    g.db.add(ma)

    return redirect(f"/+{board.name}/mod/appearance?msg=Success")


@app.route("/mod/approve/<bid>", methods=["POST"])
@auth_required
@is_guildmaster("access")
@validate_formkey
def mod_approve_bid_user(bid, board, v):

    user = get_user(request.form.get("username"), graceful=True)

    if not user:
        return jsonify({"error": "That user doesn't exist."}), 404

    if board.has_ban(user):
        return jsonify({"error": f"@{user.username} is exiled from +{board.name} and can't currently be approved."}), 409
    if board.has_contributor(user):
        return jsonify({"error": f"@{user.username} is already an approved user."})

    # check for an existing deactivated approval
    existing_contrib = g.db.query(ContributorRelationship).filter_by(
        user_id=user.id, board_id=board.id, is_active=False).first()
    if existing_contrib:
        existing_contrib.is_active = True
        existing_contrib.created_utc = int(time.time())
        existing_contrib.approving_mod_id = v.id
        g.db.add(existing_contrib)
    else:
        new_contrib = ContributorRelationship(user_id=user.id,
                                              board_id=board.id,
                                              is_active=True,
                                              approving_mod_id=v.id)
        g.db.add(new_contrib)
        g.db.commit()

        if user.id != v.id:
            text = f"You have been added as an approved contributor to +{board.name}."
            send_notification(user, text)

    ma=ModAction(
        kind="contrib_user",
        user_id=v.id,
        board_id=board.id,
        target_user_id=user.id
        )
    g.db.add(ma)

    return "", 204


@app.route("/mod/unapprove/<bid>", methods=["POST"])
@auth_required
@is_guildmaster("access")
@validate_formkey
def mod_unapprove_bid_user(bid, board, v):

    user = get_user(request.values.get("username"))

    x = board.has_contributor(user)
    if not x:
        abort(409)

    if not x.board_id==board.id:
        abort(400)

    x.is_active = False

    g.db.add(x)
    g.db.commit()
    ma=ModAction(
        kind="uncontrib_user",
        user_id=v.id,
        board_id=board.id,
        target_user_id=user.id
        )
    g.db.add(ma)
    return "", 204


@app.route("/+<guild>/pic/profile")
@limiter.exempt
def guild_profile(guild):
    x = get_guild(guild)

    if x.over_18:
        return redirect("/assets/images/icons/nsfw_guild_icon.png")
    else:
        return redirect(x.profile_url)


@app.route("/siege_guild", methods=["POST"])
@is_not_banned
@validate_formkey
def siege_guild(v):

    now = int(time.time())
    guild = request.form.get("guild", None)

    if not guild:
        abort(400)

    guild = get_guild(guild)

    # check time
    if v.last_siege_utc > now - (60 * 60 * 24 * 30):
        return render_template("message.html",
                               v=v,
                               title=f"Siege against +{guild.name} Failed",
                               error="You need to wait 30 days between siege attempts."
                               ), 403

    # update siege date
    v.last_siege_utc = now
    g.db.add(v)
    for alt in v.alts:
        alt.last_siege_utc = now
        g.db.add(v)

    # check guild count
    if not v.can_join_gms and guild not in v.boards_modded:
        return render_template("message.html",
                               v=v,
                               title=f"Siege against +{guild.name} Failed",
                               error="You already lead the maximum number of guilds."
                               ), 403

    # Cannot siege +general, +ruqqus, +ruqquspress, +ruqqusdmca
    if not guild.is_siegable:
        return render_template("message.html",
                               v=v,
                               title=f"Siege against +{guild.name} Failed",
                               error=f"+{guild.name} is an admin-controlled guild and is immune to siege. You may try again in 30 days."
                               ), 403

    # check user activity
    # karma=sum([x.score_top for x in v.submissions.filter_by(board_id=guild.id)])
    # karma+=sum([x.score_top for x in v.comments.filter_by(board_id=guild.id)])
# if karma < 100:
# return render_template("message.html",
# v=v,
# title=f"Siege against +{guild.name} Failed",
# error=f"You do not have enough Reputation in +{guild.name} to siege it. You may try again in 30 days."
# ), 403

    # Assemble list of mod ids to check
    # skip any user with a perm site-wide ban
    # skip any deleted mod
    mods = [x for x in guild.mods if not x.is_deleted]

    # if no mods, skip straight to success
    if mods:

        ids = [x.id for x in mods]

        # cutoff
        cutoff = now - 60 * 60 * 24 * 60

        # check submissions

        if g.db.query(Submission).filter(Submission.author_id.in_(
                ids), Submission.created_utc > cutoff).first():
            return render_template("message.html",
                                   v=v,
                                   title=f"Siege against +{guild.name} Failed",
                                   error="Your siege failed. One of the guildmasters has post or comment activity in the last 60 days. You may try again in 30 days."
                                   ), 403

        # check comments
        if g.db.query(Comment).filter(Comment.author_id.in_(ids),
                                      Comment.created_utc > cutoff).first():
            return render_template("message.html",
                                   v=v,
                                   title=f"Siege against +{guild.name} Failed",
                                   error="Your siege failed. One of the guildmasters has post or comment activity in the last 60 days. You may try again in 30 days."
                                   ), 403

        # check post votes
        if g.db.query(Vote).filter(Vote.user_id.in_(ids),
                                   Vote.created_utc > cutoff).first():
            return render_template("message.html",
                                   v=v,
                                   title=f"Siege against +{guild.name} Failed",
                                   error="Your siege failed. One of the guildmasters has voting activity in the last 60 days. You may try again in 30 days."
                                   ), 403

        # check comment votes
        if g.db.query(CommentVote).filter(CommentVote.user_id.in_(
                ids), CommentVote.created_utc > cutoff).first():
            return render_template("message.html",
                                   v=v,
                                   title=f"Siege against +{guild.name} Failed",
                                   error="Your siege failed. One of the guildmasters has voting activity in the last 60 days. You may try again in 30 days."
                                   ), 403

        # check flags
        if g.db.query(Flag).filter(Flag.user_id.in_(ids),
                                   Flag.created_utc > cutoff).first():
            return render_template("message.html",
                                   v=v,
                                   title=f"Siege against +{guild.name} Failed",
                                   error="Your siege failed. One of the guildmasters has private activity in the last 60 days. You may try again in 30 days."
                                   ), 403
        # check reports
        if g.db.query(Report).filter(Report.user_id.in_(ids),
                                     Report.created_utc > cutoff).first():
            return render_template("message.html",
                                   v=v,
                                   title=f"Siege against +{guild.name} Failed",
                                   error="Your siege failed. One of the guildmasters has private activity in the last 60 days. You may try again in 30 days."
                                   ), 403

        # check exiles
        if g.db.query(BanRelationship).filter(BanRelationship.banning_mod_id.in_(
                ids), BanRelationship.created_utc > cutoff).first():
            return render_template("message.html",
                                   v=v,
                                   title=f"Siege against +{guild.name} Failed",
                                   error="Your siege failed. One of the guildmasters has private activity in the last 60 days. You may try again in 30 days."
                                   ), 403

    #Siege is successful

    # delete and notify mods
    for x in guild.moderators:

        if x.accepted:
            send_notification(x.user,
                              f"You have been overthrown from +{guild.name}.")


            ma=ModAction(
                kind="remove_mod",
                user_id=1,
                board_id=guild.id,
                target_user_id=x.user_id,
                note="siege"
            )
            g.db.add(ma)
        else:
            ma=ModAction(
                kind="uninvite_mod",
                user_id=1,
                board_id=guild.id,
                target_user_id=x.user_id,
                note="siege"
            )
            g.db.add(ma)

        g.db.delete(x)

    # add new mod if user is not already
    m=guild.has_mod(v)
    if not m:
        new_mod = ModRelationship(user_id=v.id,
                                  board_id=guild.id,
                                  created_utc=now,
                                  accepted=True,
                                  perm_full=True,
                                  perm_access=True,
                                  perm_appearance=True,
                                  perm_content=True,
                                  perm_config=True
                                  )

        g.db.add(new_mod)
        ma=ModAction(
            kind="add_mod",
            user_id=1,
            board_id=guild.id,
            target_user_id=v.id,
            note="siege"
        )
        g.db.add(ma)

    elif not m.perm_full:
        for p in m.__dict__:
            if p.startswith("perm_"):
                m.__dict__[p]=True
        g.db.add(p)
        ma=ModAction(
            kind="change_perms",
            user_id=1,
            board_id=guild.id,
            target_user_id=v.id,
            note="siege"
        )
        g.db.add(ma)        

    return redirect(f"/+{guild.name}/mod/mods")


@app.route("/mod/post_pin/<bid>/<pid>/<x>", methods=["POST"])
@auth_required
@is_guildmaster("content")
@validate_formkey
def mod_toggle_post_pin(bid, pid, x, board, v):

    post = get_post(pid)

    if post.board_id != board.id:
        abort(400)

    try:
        x = bool(int(x))
    except BaseException:
        abort(400)

    if x and not board.can_pin_another:
        return jsonify({"error": f"+{board.name} already has the maximum number of pinned posts."}), 409

    post.is_pinned = x

    cache.delete_memoized(Board.idlist, post.board)

    g.db.add(post)

    ma=ModAction(
        kind="pin_post" if post.is_pinned else "unpin_post",
        user_id=v.id,
        board_id=board.id,
        target_submission_id=post.id
    )
    g.db.add(ma)

    return "", 204


@app.route("/+<boardname>/comments")
@app.route("/api/v1/guild/<boardname>/comments")
@auth_desired
@api("read")
def board_comments(boardname, v):

    b = get_guild(boardname)

    page = int(request.args.get("page", 1))

    idlist = b.comment_idlist(v=v,
                              page=page,
                              nsfw=v and v.over_18,
                              nsfl=v and v.show_nsfl,
                              hide_offensive=v and v.hide_offensive)

    next_exists = len(idlist) == 26

    idlist = idlist[0:25]

    comments = get_comments(idlist, v=v)

    return {"html": lambda: render_template("board_comments.html",
                                            v=v,
                                            b=b,
                                            page=page,
                                            comments=comments,
                                            standalone=True,
                                            next_exists=next_exists),
            "api": lambda: jsonify({"data": [x.json for x in comments]})}


@app.route("/mod/<bid>/category/<category>", methods=["POST"])
@auth_required
@is_guildmaster("config")
@validate_formkey
def change_guild_category(v, board, bid, category):

    category = int(category)

    sc=g.db.query(SubCategory).filter_by(id=category).first()
    if not sc:
        return jsonify({"error": f"Invalid category id"}), 400

    if board.is_locked_category:
        return jsonify({"error": "You can't do that right now."}), 403

    board.subcat_id=sc.id
    g.db.add(board)
    g.db.flush()

    ma=ModAction(
        kind="update_settings",
        user_id=v.id,
        board_id=board.id,
        note=f"category={sc.category.name} / {sc.name}"
    )
    g.db.add(ma)

    return jsonify({"message": f"Category changed to {sc.category.name} / {sc.name}"})



@app.route("/+<boardname>/mod/log", methods=["GET"])
@auth_desired
def board_mod_log(boardname, v):

    page=int(request.args.get("page",1))
    board=get_guild(boardname)

    actions=g.db.query(ModAction).filter_by(board_id=board.id).order_by(ModAction.id.desc()).offset(25*(page-1)).limit(26).all()
    actions=[i for i in actions]

    next_exists=len(actions)==26
    actions=actions[0:25]

    return render_template("guild/modlog.html",
        v=v,
        b=board,
        actions=actions,
        next_exists=next_exists,
        page=page
        )

@app.route("/+<boardname>/mod/log/<aid>", methods=["GET"])
@auth_desired
def mod_log_item(boardname, aid, v):

    action=g.db.query(ModAction).filter_by(id=base36decode(aid)).first()

    if not action:
        abort(404)

    if request.path != action.permalink:
        return redirect(action.permalink)

    return render_template("guild/modlog.html",
        v=v,
        b=action.board,
        actions=[action],
        next_exists=False,
        page=1,
        action=action
        )

@app.route("/+<boardname>/mod/edit_perms", methods=["POST"])
@auth_required
@is_guildmaster("full")
@validate_formkey
def board_mod_perms_change(boardname, board, v):

    user=get_user(request.form.get("username"))

    v_mod=board.has_mod(v)
    u_mod=board.has_mod_record(user)

    if v_mod.id > u_mod.id:
        return jsonify({"error":"You can't change perms on guildmasters above you."}), 403

    #print({x:request.form.get(x) for x in request.form})

    u_mod.perm_full         = bool(request.form.get("perm_full"         , False))
    u_mod.perm_access       = bool(request.form.get("perm_access"       , False))
    u_mod.perm_appearance   = bool(request.form.get("perm_appearance"   , False))
    u_mod.perm_config       = bool(request.form.get("perm_config"       , False))
    u_mod.perm_content      = bool(request.form.get("perm_content"      , False))

    g.db.add(u_mod)
    g.db.commit()

    ma=ModAction(
        kind="change_perms" if u_mod.accepted else "change_invite",
        user_id=v.id,
        board_id=board.id,
        target_user_id=user.id,
        note=u_mod.permchangelist
    )
    g.db.add(ma)

    return redirect(f"{board.permalink}/mod/mods")