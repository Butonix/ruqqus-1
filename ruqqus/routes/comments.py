from urllib.parse import urlparse
import mistletoe
from sqlalchemy import func, literal
from bs4 import BeautifulSoup

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.filters import *
from ruqqus.helpers.embed import *
from ruqqus.helpers.markdown import *
from ruqqus.helpers.get import *
from ruqqus.helpers.session import *
from ruqqus.classes import *
from flask import *
from ruqqus.__main__ import app, limiter
from werkzeug.contrib.atom import AtomFeed
from datetime import datetime




@app.route("/comment/<cid>", methods=["GET"])
def comment_cid(cid):

    comment=get_comment(cid)
    if not comment.parent_submission:
        abort(403)
    return redirect(comment.permalink)

@app.route("/post/<p_id>/<anything>/<c_id>", methods=["GET"])
@app.route("/api/v1/post/<p_id>/comment/<c_id>", methods=["GET"])
@auth_desired
@api("read")
def post_pid_comment_cid(p_id, c_id, anything=None, v=None):

    comment=get_comment(c_id, v=v)

    post=get_post(p_id, v=v)

    if comment.parent_submission != post.id:
        abort(404)

    board=post.board

    if board.is_banned and not (v and v.admin_level > 3):
        return {'html':lambda:render_template("board_banned.html",
                               v=v,
                               b=board),

                'api':lambda:{'error':f'+{board.name} is banned.'}

                }

    if post.over_18 and not (v and v.over_18) and not session_over18(comment.board):
        t=int(time.time())
        return {'html':lambda:render_template("errors/nsfw.html",
                               v=v,
                               t=t,
                               lo_formkey=make_logged_out_formkey(t),
                               board=comment.board
                               ),
                'api':lambda:{'error':f'This content is not suitable for some users and situations.'}

                }

    if post.is_nsfl and not (v and v.show_nsfl) and not session_isnsfl(comment.board):
        t=int(time.time())
        return {'html':lambda:render_template("errors/nsfl.html",
                               v=v,
                               t=t,
                               lo_formkey=make_logged_out_formkey(t),
                               board=comment.board
                               ),

                'api':lambda:{'error':f'This content is not suitable for some users and situations.'}

                }


    #check guild ban
    board=post.board
    if board.is_banned and v.admin_level<3:
        return {'html':lambda:render_template("board_banned.html",
                               v=v,
                               b=board),
                'api':lambda:{'error':f'+{board.name} is banned.'}
                }

    post._preloaded_comments=[comment]

    #context improver
    context=min(int(request.args.get("context", 0)), 4)
    c=comment
    while context > 0 and not c.is_top_level:

        parent=get_comment(c.parent_comment_id, v=v)

        post._preloaded_comments+=[parent]

        c=parent
        context -=1
    top_comment=c

    sort_type=request.args.get("sort", "hot")
    #children comments
    current_ids=[comment.id]
    for i in range(6-context):
        if v:
            votes=g.db.query(CommentVote).filter(CommentVote.user_id==v.id).subquery()

            blocking=v.blocking.subquery()
            blocked=v.blocked.subquery()

            comms=g.db.query(
                Comment,
                votes.c.vote_type,
                blocking.c.id,
                blocked.c.id
                ).select_from(Comment).options(
                joinedload(Comment.author).joinedload(User.title)
                ).filter(
                Comment.parent_comment_id.in_(current_ids)
                ).join(
                votes,
                votes.c.comment_id==Comment.id,
                isouter=True
                ).join(
                blocking,
                blocking.c.target_id==Comment.author_id,
                isouter=True
                ).join(
                blocked,
                blocked.c.user_id==Comment.author_id,
                isouter=True
                )

            if sort_type=="hot":
                comments=comms.order_by(Comment.score_hot.asc()).all()
            elif sort_type=="top":
                comments=comms.order_by(Comment.score_top.asc()).all()
            elif sort_type=="new":
                comments=comms.order_by(Comment.created_utc.desc()).all()
            elif sort_type=="disputed":
                comments=comms.order_by(Comment.score_disputed.asc()).all()
            elif sort_type=="random":
                c=comms.all()
                comments=random.sample(c, k=len(c))
            else:
                abort(422)


            output=[]
            for c in comms:
                comment=c[0]
                comment._voted=c[1] or 0
                comment._is_blocking=c[2] or 0
                comment._is_blocked=c[3] or 0
                output.append(comment)
        else:

            comms=g.db.query(
                Comment
                ).options(
                joinedload(Comment.author).joinedload(User.title)
                ).filter(
                Comment.parent_comment_id.in_(current_ids)
                )

            if sort_type=="hot":
                comments=comms.order_by(Comment.score_hot.asc()).all()
            elif sort_type=="top":
                comments=comms.order_by(Comment.score_top.asc()).all()
            elif sort_type=="new":
                comments=comms.order_by(Comment.created_utc.desc()).all()
            elif sort_type=="disputed":
                comments=comms.order_by(Comment.score_disputed.asc()).all()
            elif sort_type=="random":
                c=comms.all()
                comments=random.sample(c, k=len(c))
            else:
                abort(422)

            output=[c for c in comms]

        post._preloaded_comments+=output

        current_ids=[x.id for x in output]

        
    return {'html':lambda:post.rendered_page(v=v, comment=top_comment, comment_info=comment),
            'api':lambda:c.json
            }

@app.route("/api/comment", methods=["POST"])
@app.route("/api/v1/comment", methods=["POST"])
@limiter.limit("6/minute")
@is_not_banned
@tos_agreed
@validate_formkey
@api("create")
def api_comment(v):

    parent_submission=base36decode(request.form.get("submission"))
    parent_fullname=request.form.get("parent_fullname")
    parent_post=get_post(request.form.get("submission"))

    #process and sanitize
    body=request.form.get("body","")[0:10000]
    body=body.lstrip().rstrip()

    with CustomRenderer(post_id=request.form.get("submission")) as renderer:
        body_md=renderer.render(mistletoe.Document(body))
    body_html=sanitize(body_md, linkgen=True)

    #Run safety filter
    bans=filter_comment_html(body_html)

    if bans:
        ban=bans[0]
        reason=f"Remove the {ban.domain} link from your comment and try again."
        if ban.reason:
          reason += f" {ban.reason_text}"
        return jsonify({"error": reason}), 401



    #get parent item info
    parent_id=parent_fullname.split("_")[1]
    if parent_fullname.startswith("t2"):
        parent=parent_post
        parent_comment_id=None
        level=1
    elif parent_fullname.startswith("t3"):
        parent=get_comment(parent_id, v=v)
        parent_comment_id=parent.id
        level=parent.level+1
        if parent.parent_submission!=parent_submission:
            abort(400)

    #check existing
    existing=g.db.query(Comment).join(CommentAux).filter(Comment.author_id==v.id,
                                         Comment.is_deleted==False,
                                         Comment.parent_comment_id==parent_comment_id,
                                         Comment.parent_submission==parent_submission,
                                         CommentAux.body==body
                                         ).options(contains_eager(Comment.comment_aux)).first()
    if existing:
        return jsonify({"error":f"You already made that comment: {existing.permalink}"}), 409

    #No commenting on deleted/removed things
    if parent.is_banned or parent.is_deleted:
        return jsonify({"error":"You can't comment on things that have been deleted."}), 403

    if parent.author.any_block_exists(v):
        return jsonify({"error":"You can't reply to users who have blocked you, or users you have blocked."}), 403

    #check for archive and ban state
    post = get_post(request.form.get("submission"))
    if post.is_archived or not post.board.can_comment(v):
        return jsonify({"error":"You can't comment on this."}), 403

    #check spam - this is stupid slow for now
    #similar_comments=g.db.query(Comment).filter(Comment.author_id==v.id, CommentAux.body.op('<->')(body)<0.5).options(contains_eager(Comment.comment_aux)).all()
    #print(similar_comments)

    for x in g.db.query(BadWord).all():
        if x.check(body):
            is_offensive=True
            break
        else:
            is_offensive=False

    #check badlinks
    soup=BeautifulSoup(body_html, features="html.parser")
    links=[x['href'] for x in soup.find_all('a') if x.get('href')]

    for link in links:
        parse_link=urlparse(link)
        check_url=ParseResult(scheme="https",
                            netloc=parse_link.netloc,
                            path=parse_link.path,
                            params=parse_link.params,
                            query=parse_link.query,
                            fragment='')
        check_url=urlunparse(check_url)


        badlink=g.db.query(BadLink).filter(literal(check_url).contains(BadLink.link)).first()

        if badlink:
            return jsonify({"error":f"Remove the following link and try again: `{check_url}`. Reason: {badlink.reason_text}"}), 403
        
    #create comment
    c=Comment(author_id=v.id,
              parent_submission=parent_submission,
              parent_fullname=parent_fullname,
              parent_comment_id=parent_comment_id,
              level=level,
              over_18=post.over_18,
              is_nsfl=post.is_nsfl,
              is_op=(v.id==post.author_id),
              is_offensive=is_offensive,
              original_board_id=parent_post.board_id
              )

    g.db.add(c)
    g.db.flush()


       
    c_aux=CommentAux(
      id=c.id,
      body_html=body_html,
      body=body
      )
    g.db.add(c_aux)
    g.db.flush()

    notify_users=set()

    #queue up notification for parent author
    if parent.author.id != v.id:
        notify_users.add(parent.author.id)

    #queue up notifications for username mentions
    soup=BeautifulSoup(body_html, features="html.parser")
    mentions=soup.find_all("a", href=re.compile("^/@(\w+)"), limit=3)
    for mention in mentions:
        username=mention["href"].split("@")[1]

        user=g.db.query(User).filter_by(username=username).first()

        if user:
            if v.any_block_exists(user):
                continue
            if user.id != v.id:
                notify_users.add(user.id)


    for x in notify_users:
        n=Notification(comment_id=c.id,
                       user_id=x)
        g.db.add(n)
    


    #create auto upvote
    vote=CommentVote(user_id=v.id,
                     comment_id=c.id,
                     vote_type=1
                     )

    g.db.add(vote)

    g.db.commit()
    

    #print(f"Content Event: @{v.username} comment {c.base36id}")

    return {"html":lambda:jsonify({"html":render_template("comments.html",
                                           v=v, 
                                           comments=[c], 
                                           render_replies=False,
                                           is_allowed_to_comment=True
                                           )}),
            "api":lambda:c.json
            }
    

@app.route("/edit_comment/<cid>", methods=["POST"])
@is_not_banned
@validate_formkey
@api("edit")
def edit_comment(cid, v):

    c = get_comment(cid, v=v)

    if not c.author_id == v.id:
        abort(403)

    if c.is_banned or c.is_deleted:
        abort(403)

    if c.board.has_ban(v):
        abort(403)
        
    body = request.form.get("body", "")[0:10000]
    with CustomRenderer(post_id=c.post.base36id) as renderer:
        body_md=renderer.render(mistletoe.Document(body))
    body_html = sanitize(body_md, linkgen=True)

    #Run safety filter
    bans=filter_comment_html(body_html)

    if bans:
        return {'html':lambda:render_template("comment_failed.html",
                               action=f"/edit_comment/{c.base36id}",
                               badlinks=[x.domain for x in bans],
                               body=body,
                               v=v
                               ),
                'api':lambda:({'error':f'A blacklisted domain was used.'}, 400)
                }

    for x in g.db.query(BadWord).all():
        if x.check(body):
            c.is_offensive=True
            break
        else:
            c.is_offensive=False

    c.body=body
    c.body_html=body_html
    c.edited_utc = int(time.time())

    g.db.add(c)
    
    g.db.commit()

    path=request.form.get("current_page","/")

    return jsonify({"html":c.body_html})

@app.route("/delete/comment/<cid>", methods=["POST"])
@app.route("/api/v1/delete/comment/<cid>", methods=["POST"])
@auth_required
@validate_formkey
@api("delete")
def delete_comment(cid, v):

    c=g.db.query(Comment).filter_by(id=base36decode(cid)).first()

    if not c:
        abort(404)

    if not c.author_id==v.id:
        abort(403)

    c.is_deleted=True

    g.db.add(c)
    

    cache.delete_memoized(User.commentlisting, v)

    return {"html":lambda:("", 204),
        "api":lambda:("", 204)}



@app.route("/embed/comment/<cid>", methods=["GET"])
@app.route("/embed/post/<pid>/comment/<cid>", methods=["GET"])
@app.route("/api/v1/embed/comment/<cid>", methods=["GET"])
@app.route("/api/v1/embed/post/<pid>/comment/<cid>", methods=["GET"])
def embed_comment_cid(cid, pid=None):

    comment=get_comment(cid)

    if not comment.parent:
        abort(403)

    if comment.is_banned or comment.is_deleted:
        return {'html':lambda:render_template("embeds/comment_removed.html", c=comment),
                'api':lambda:{'error':f'Comment {cid} has been removed'}
               }

    if comment.board.is_banned:
        abort(410)

    return render_template("embeds/comment.html", c=comment)

