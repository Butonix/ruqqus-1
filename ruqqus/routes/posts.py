from urllib.parse import urlparse, ParseResult, urlunparse, urlencode
import mistletoe
from sqlalchemy import func
from bs4 import BeautifulSoup
import secrets
import threading
import requests

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.filters import *
from ruqqus.helpers.embed import *
from ruqqus.helpers.markdown import *
from ruqqus.helpers.get import *
from ruqqus.helpers.thumbs import *
from ruqqus.helpers.session import *
from ruqqus.helpers.aws import *
from ruqqus.classes import *
from .front import frontlist
from flask import *
from ruqqus.__main__ import app, db, limiter, cache

BAN_REASONS=['',
             "URL shorteners are not permitted.",
             "Pornographic material is not permitted.",
             "Copyright infringement is not permitted."
            ]

BUCKET="i.ruqqus.com"






@app.route("/post/<base36id>", methods=["GET"])
@auth_desired
def post_base36id(base36id, v=None):
    
    post=get_post(base36id)

    board=post.board

    if board.is_banned and not (v and v.admin_level > 3):
        return render_template("board_banned.html",
                               v=v,
                               b=board,
                               p=True)

    if post.over_18 and not (v and v.over_18) and not session_over18(board):
        t=int(time.time())
        return render_template("errors/nsfw.html",
                               v=v,
                               t=t,
                               lo_formkey=make_logged_out_formkey(t),
                               board=post.board
                               )
        
    return post.rendered_page(v=v)

@app.route("/submit", methods=["GET"])
@is_not_banned
def submit_get(v):

    board=request.args.get("guild","general")
    b=get_guild(board, graceful=True)
    if not b:
        b=get_guild("general")
    
    return render_template("submit.html",
                           v=v,
                           b=b
                           )


@app.route("/edit_post/<pid>", methods=["POST"])
@is_not_banned
@validate_formkey
def edit_post(pid, v):
    
    p = get_post(pid)

    if not p.author_id == v.id:
        abort(403)

    if p.is_banned:
        abort(403)

    if p.board.has_ban(v):
        abort(403)

    body = request.form.get("body", "")
    with CustomRenderer() as renderer:
        body_md = renderer.render(mistletoe.Document(body))
    body_html = sanitize(body_md, linkgen=True)

    p.body = body
    p.body_html = body_html
    p.edited_utc = int(time.time())

    db.add(p)
    db.commit()

    return redirect(p.permalink)

@app.route("/api/submit/title", methods=['GET'])
@limiter.limit("6/minute")
@is_not_banned
#@tos_agreed
#@validate_formkey
def get_post_title(v):

    url=request.args.get("url",None)
    if not url:
        return abort(400)

    headers={"User-Agent":app.config["UserAgent"]}
    try:
        x=requests.get(url, headers=headers)
    except:
        return jsonify({"error": "Could not reach page"}), 400
    
    if not x.status_code==200:
        return jsonify({"error":f"Page returned {x.status_code}"}), x.status_code

    try:
        soup = BeautifulSoup(x.content, 'html.parser')

        data={"url":url,
              "title":soup.find('title').string
              }

        return jsonify(data)
    except:
        return jsonify({"error":f"Could not find a title"}), 400



@app.route("/submit", methods=['POST'])
@limiter.limit("6/minute")
@is_not_banned
@tos_agreed
@validate_formkey
def submit_post(v):

    title=request.form.get("title","")

    url=request.form.get("url","")

    if len(title)<10:
        return render_template("submit.html",
                               v=v,
                               error="Please enter a better title.",
                               title=title,
                               url=url,
                               body=request.form.get("body",""),
                               b=get_guild(request.form.get("board",""),
                                           graceful=True
                                           )
                               )
    elif len(title)>250:
        return render_template("submit.html",
                               v=v,
                               error="250 character limit for titles.",
                               title=title[0:250],
                               url=url,
                               body=request.form.get("body",""),
                               b=get_guild(request.form.get("board",""),
                                           graceful=True
                                           )
                               )

    parsed_url=urlparse(url)
    if not (parsed_url.scheme and parsed_url.netloc) and not request.form.get("body") and not request.files.get("file",None):
        return render_template("submit.html",
                               v=v,
                               error="Please enter a URL or some text.",
                               title=title,
                               url=url,
                               body=request.form.get("body",""),
                               b=get_guild(request.form.get("board","")
                                           )
                               )

    #sanitize title
    title=sanitize(title, linkgen=False)

    #check for duplicate
    dup = db.query(Submission).filter_by(title=title,
                                         author_id=v.id,
                                         url=url,
                                         is_deleted=False
                                         ).first()

    if dup:
        return redirect(dup.permalink)

    
    #check for domain specific rules

    parsed_url=urlparse(url)

    domain=parsed_url.netloc

    # check ban status
    domain_obj=get_domain(domain)
    if domain_obj:
        if not domain_obj.can_submit:
            return render_template("submit.html",
                                   v=v,
                                   error=BAN_REASONS[domain_obj.reason],
                                   title=title,
                                   url=url,
                                   body=request.form.get("body",""),
                                   b=get_guild(request.form.get("board","general"),
                                           graceful=True)
                                   )

        #check for embeds
        if domain_obj.embed_function:
            try:
                embed=eval(domain_obj.embed_function)(url)
            except:
                embed=""
        else:
            embed=""
    else:
        embed=""
        

    #board
    board_name=request.form.get("board","general")
    board_name=board_name.lstrip("+")
    
    board=get_guild(board_name, graceful=True)
    
    if not board:
        board=get_guild('general')

    if board.is_banned:
        return render_template("submit.html",
                               v=v,
                               error=f"+{board.name} has been demolished.",
                               title=title,
                               url=url
                               , body=request.form.get("body",""),
                               b=get_guild("general",
                                           graceful=True)
                               ), 403       
    
    if board.has_ban(v):
        return render_template("submit.html",
                               v=v,
                               error=f"You are exiled from +{board.name}.",
                               title=title,
                               url=url
                               , body=request.form.get("body",""),
                               b=get_guild("general")
                               ), 403

    if (board.restricted_posting or board.is_private) and not (board.can_submit(v)):
        return render_template("submit.html",
                               v=v,
                               error=f"You are not an approved contributor for +{board.name}.",
                               title=title,
                               url=url,
                               body=request.form.get("body",""),
                               b=get_guild(request.form.get("board","general"),
                                           graceful=True
                                           )
                               )
    user_id=v.id
    user_name=v.username
                
                
    #Force https for submitted urls
    if request.form.get("url"):
        new_url=ParseResult(scheme="https",
                            netloc=parsed_url.netloc,
                            path=parsed_url.path,
                            params=parsed_url.params,
                            query=parsed_url.query,
                            fragment=parsed_url.fragment)
        url=urlunparse(new_url)
    else:
        url=""

    #now make new post

    body=request.form.get("body","")

    #catch too-long body
    if len(body)>10000:

        return render_template("submit.html",
                               v=v,
                               error="10000 character limit for text body",
                               title=title,
                               text=body[0:10000],
                               url=url,
                               b=get_guild(request.form.get("board","general"),
                                           graceful=True
                                           )
                               ), 400

    if len(url)>2048:

        return render_template("submit.html",
                               v=v,
                               error="URLs cannot be over 2048 characters",
                               title=title,
                               text=body[0:2000],
                               b=get_guild(request.form.get("board","general"),
                                           graceful=True)
                               ), 400

    with CustomRenderer() as renderer:
        body_md=renderer.render(mistletoe.Document(body))
    body_html = sanitize(body_md, linkgen=True)

    #check for embeddable video
    domain=parsed_url.netloc



    
    
    new_post=Submission(title=title,
                        url=url,
                        author_id=user_id,
                        body=body,
                        body_html=body_html,
                        embed_url=embed,
                        domain_ref=domain_obj.id if domain_obj else None,
                        board_id=board.id,
                        original_board_id=board.id,
                        over_18=(bool(request.form.get("over_18","")) or board.over_18),
                        post_public=not board.is_private,
                        author_name=user_name,
                        guild_name=board.name
                        )

    db.add(new_post)

    db.commit()

    new_post.determine_offensive()

    vote=Vote(user_id=user_id,
              vote_type=1,
              submission_id=new_post.id
              )
    db.add(vote)
    db.commit()

    #check for uploaded image
    if request.files.get('file'):
        file=request.files['file']

        name=f'post/{new_post.base36id}/{secrets.token_urlsafe(8)}'

        upload_file(name, file)
        
        #update post data
        new_post.url=f'https://{BUCKET}/{name}'
        new_post.is_image=True
        db.add(new_post)
        db.commit()

    
    #spin off thumbnail generation and csam detection as  new threads
    elif new_post.url:
        new_thread=threading.Thread(target=thumbnail_thread,
                                    args=(new_post.base36id,)
                                    )
        new_thread.start()
        csam_thread = threading.Thread(target=check_csam, args=(new_post,))
        csam_thread.start()

    #expire the relevant caches: front page new, board new
    cache.delete_memoized(frontlist, sort="new")
    cache.delete_memoized(Board.idlist, board, sort="new")

    #print(f"Content Event: @{new_post.author.username} post {new_post.base36id}")

    return redirect(new_post.permalink)
    
@app.route("/api/nsfw/<pid>/<x>", methods=["POST"])
@auth_required
@validate_formkey
def api_nsfw_pid(pid, x, v):

    try:
        x=bool(int(x))
    except:
        abort(400)

    post=get_post(pid)

    if not v.admin_level >=3 and not post.author_id==v.id and not post.board.has_mod(v):
        abort(403)
        
    post.over_18=x
    db.add(post)
    db.commit()

    return "", 204

@app.route("/delete_post/<pid>", methods=["POST"])
@auth_required
@validate_formkey
def delete_post_pid(pid, v):

    post=get_post(pid)
    if not post.author_id==v.id:
        abort(403)

    post.is_deleted=True
    
    db.add(post)

    #clear cache
    cache.delete_memoized(User.idlist, v, sort="new")

    if post.age >= 3600*6:
        cache.delete_memoized(Board.idlist, post.board, sort="new")
        cache.delete_memoized(frontlist, sort="new")
    

    #delete i.ruqqus.com
    if post.domain=="i.ruqqus.com":
        
        segments=post.url.split("/")
        pid=segments[4]
        rand=segments[5]
        if pid==post.base36id:
            key=f"post/{pid}/{rand}"
            delete_file(key)
            post.is_image=False
            db.add(post)
            
    db.commit()
        

    return "",204


@app.route("/embed/post/<pid>", methods=["GET"])
def embed_post_pid(pid):

    post=get_post(pid)

    if post.is_banned or post.board.is_banned:
        abort(410)

    return render_template("embeds/submission.html", p=post)

@app.route("/api/toggle_post_nsfw/<pid>", methods=["POST"])
@is_not_banned
@validate_formkey
def toggle_post_nsfw(pid, v):

    post=get_post(pid)

    if not post.author_id==v.id:
        abort(403)

    if post.board.over_18 and post.over_18:
        abort(403)

    post.over_18 = not post.over_18
    db.add(post)
    db.commit()

    return "", 204

@app.route("/api/toggle_post_nsfl/<pid>", methods=["POST"])
@is_not_banned
@validate_formkey
def toggle_post_nsfl(pid, v):

    post=get_post(pid)

    if not post.author_id==v.id:
        abort(403)

    if post.board.is_nsfl and post.is_nsfl:
        abort(403)

    post.is_nsfl = not post.is_nsfl
    db.add(post)
    db.commit()

    return "", 204
