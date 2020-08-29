from urllib.parse import urlparse, ParseResult, urlunparse, urlencode
import mistletoe
from sqlalchemy import func
from sqlalchemy.orm import aliased
from bs4 import BeautifulSoup
import secrets
import threading
import requests
import re
import bleach
import time

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
from ruqqus.helpers.alerts import send_notification
from ruqqus.classes import *
from .front import frontlist
from flask import *
from ruqqus.__main__ import app, limiter, cache

BAN_REASONS=['',
             "URL shorteners are not permitted.",
             "Pornographic material is not permitted.",  #defunct
             "Copyright infringement is not permitted."
            ]

BUCKET="i.ruqqus.com"

@app.route("/post_short/", methods=["GET"])
@app.route("/post_short/<base36id>", methods=["GET"])
def incoming_post_shortlink(base36id=None):

  if not base36id:
    return redirect('/')

  post=get_post(base36id)
  return redirect(post.permalink)

@app.route("/post/<base36id>", methods=["GET"])
@app.route("/post/<base36id>/", methods=["GET"])
@app.route("/post/<base36id>/<anything>", methods=["GET"])
@auth_desired
def post_base36id(base36id, anything=None, v=None):
    
    post=get_post_with_comments(base36id, v=v, sort_type=request.args.get("sort","top"))

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

    #offensive
    p.is_offensive=False
    for x in g.db.query(BadWord).all():
        if (p.body and x.check(p.body)) or x.check(p.title):
            p.is_offensive=True
            break   

    return redirect(p.permalink)

@app.route("/api/submit/title", methods=['GET'])
@limiter.limit("3/minute")
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
@app.route("/api/v1/submit", methods=["POST"])
@limiter.limit("6/minute")
@is_not_banned
@tos_agreed
@validate_formkey
@api("create")
def submit_post(v):

    title=request.form.get("title","")

    title=title.lstrip().rstrip()
    title=title.replace("\n","")
    title=title.replace("\r","")
    title=title.replace("\t","")
    


    url=request.form.get("url","")

    board=get_guild(request.form.get('board','general'), graceful=True)
    if not board:
        board=get_guild('general')

    if not title:
        return render_template("submit.html",
                               v=v,
                               error="Please enter a better title.",
                               title=title,
                               url=url,
                               body=request.form.get("body",""),
                               b=board
                               )

    # if len(title)<10:
    #     return render_template("submit.html",
    #                            v=v,
    #                            error="Please enter a better title.",
    #                            title=title,
    #                            url=url,
    #                            body=request.form.get("body",""),
    #                            b=board
    #                            )
    
    elif len(title)>500:
        return render_template("submit.html",
                               v=v,
                               error="500 character limit for titles.",
                               title=title[0:500],
                               url=url,
                               body=request.form.get("body",""),
                               b=board
                               )

    parsed_url=urlparse(url)
    if not (parsed_url.scheme and parsed_url.netloc) and not request.form.get("body") and not request.files.get("file",None):
        return render_template("submit.html",
                               v=v,
                               error="Please enter a URL or some text.",
                               title=title,
                               url=url,
                               body=request.form.get("body",""),
                               b=board
                               )
    #sanitize title
    title=bleach.clean(title)

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

    body=request.form.get("body","")
    #check for duplicate
    dup = g.db.query(Submission).join(Submission.submission_aux).filter(
      Submission.author_id==v.id,
      Submission.is_deleted==False,
      Submission.board_id==board.id,
      SubmissionAux.title==title, 
      SubmissionAux.url==url,
      SubmissionAux.body==body
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
    board_name=board_name.rstrip()
    
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



    #similarity check
    now=int(time.time())
    cutoff=now-60*60*24
    similar_posts = g.db.query(Submission).options(
        lazyload('*')
        ).join(Submission.submission_aux
        ).filter(
        Submission.author_id==v.id, 
        SubmissionAux.title.op('<->')(title)<app.config["SPAM_SIMILARITY_THRESHOLD"],
        Submission.created_utc>cutoff
        ).all()

    if url:
        similar_urls=g.db.query(Submission).options(
            lazyload('*')
            ).join(Submission.submission_aux
            ).filter(
            Submission.author_id==v.id, 
            SubmissionAux.url.op('<->')(url)<app.config["SPAM_URL_SIMILARITY_THRESHOLD"],
            Submission.created_utc>cutoff
            ).all()
    else:
        similar_urls=[]

    threshold = app.config["SPAM_SIMILAR_COUNT_THRESHOLD"]
    if v.age >= (60*60*24*30):
        threshold *= 4
    elif v.age >=(60*60*24*7):
        threshold *= 3
    elif v.age >=(60*60*24):
        threshold *= 2


    if max(len(similar_urls), len(similar_posts)) >= threshold:

        text="Your Ruqqus account has been suspended for 1 day for the following reason:\n\n> Too much spam!"
        send_notification(v, text)

        v.ban(reason="Spamming.",
          include_alts=True,
          days=1)

        for post in similar_posts+similar_urls:
            post.is_banned=True
            post.ban_reason="Automatic spam removal. This happened because the post's creator submitted too much similar content too quickly."
            g.db.add(post)

        g.db.commit()
        return redirect("/notifications")

   

    #catch too-long body
    if len(str(body))>10000:

        return render_template("submit.html",
                               v=v,
                               error="10000 character limit for text body",
                               title=title,
                               text=str(body)[0:10000],
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

    #render text

    with CustomRenderer() as renderer:
        body_md=renderer.render(mistletoe.Document(body))
    body_html = sanitize(body_md, linkgen=True)


    ##check spam
    soup=BeautifulSoup(body_html, features="html.parser")
    links=[x['href'] for x in soup.find_all('a') if x.get('href')]

    if url:
        links=[url]+links

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
            if badlink.autoban:
                text="Your Ruqqus account has been suspended for 1 day for the following reason:\n\n> Too much spam!"
                send_notification(v, text)
                v.ban(days=1, reason="spam")

                return redirect('/notifications')
            else:
                return render_template("submit.html",
                           v=v,
                           error=f"The link `{badlink.link}` is not allowed. Reason: {badlink.reason}",
                           title=title,
                           text=body[0:2000],
                           b=get_guild(request.form.get("board","general"),
                                       graceful=True)
                           ), 400

    #check for embeddable video
    domain=parsed_url.netloc

    if url:
        repost = g.db.query(Submission).join(Submission.submission_aux).filter(
        SubmissionAux.url.ilike(url),
        Submission.board_id==board.id,
        Submission.is_deleted==False, 
        Submission.is_banned==False
        ).order_by(
        Submission.id.asc()
        ).first()
    else:
      repost=None

    if request.files.get('file') and not v.can_submit_image:
        abort(403)

    #offensive
    is_offensive=False
    for x in g.db.query(BadWord).all():
        if (body and x.check(body)) or x.check(title):
            is_offensive=True
            break

    new_post=Submission(author_id=v.id,
                        domain_ref=domain_obj.id if domain_obj else None,
                        board_id=board.id,
                        original_board_id=board.id,
                        over_18=(bool(request.form.get("over_18","")) or board.over_18),
                        post_public=not board.is_private,
                        repost_id=repost.id if repost else None,
                        is_offensive=is_offensive
                        )



    g.db.add(new_post)
    g.db.flush()

    new_post_aux=SubmissionAux(id=new_post.id,
                               url=url,
                               body=body,
                               body_html=body_html,
                               embed_url=embed,
                               title=title
                               )
    g.db.add(new_post_aux)
    g.db.flush()

    vote=Vote(user_id=v.id,
              vote_type=1,
              submission_id=new_post.id
              )
    g.db.add(vote)
    g.db.flush()

    g.db.commit()
    g.db.refresh(new_post)

    #check for uploaded image
    if request.files.get('file'):

        file=request.files['file']

        name=f'post/{new_post.base36id}/{secrets.token_urlsafe(8)}'
        upload_file(name, file)

        #thumb_name=f'posts/{new_post.base36id}/thumb.png'
        #upload_file(name, file, resize=(375,227))
        
        #update post data
        new_post.url=f'https://{BUCKET}/{name}'
        new_post.is_image=True
        new_post.domain_ref=1 #id of i.ruqqus.com domain
        g.db.add(new_post)
        g.db.commit()
    
    #spin off thumbnail generation and csam detection as  new threads
    if new_post.url or request.files.get('file'):
        new_thread=threading.Thread(target=thumbnail_thread,
                                    args=(new_post.base36id,)
                                    )
        new_thread.start()
        csam_thread = threading.Thread(target=check_csam, args=(new_post,))
        csam_thread.start()

    #expire the relevant caches: front page new, board new
    #cache.delete_memoized(frontlist, sort="new")
    g.db.commit()
    cache.delete_memoized(Board.idlist, board, sort="new")

    #print(f"Content Event: @{new_post.author.username} post {new_post.base36id}")

    return {"html":lambda:redirect(new_post.permalink),
            "api":lambda:jsonify(new_post.json)
            }
    
# @app.route("/api/nsfw/<pid>/<x>", methods=["POST"])
# @auth_required
# @validate_formkey
# def api_nsfw_pid(pid, x, v):

#     try:
#         x=bool(int(x))
#     except:
#         abort(400)

#     post=get_post(pid)

#     if not v.admin_level >=3 and not post.author_id==v.id and not post.board.has_mod(v):
#         abort(403)
        
#     post.over_18=x
#     g.db.add(post)
#     

#     return "", 204

@app.route("/delete_post/<pid>", methods=["POST"])
@auth_required
@validate_formkey
def delete_post_pid(pid, v):

    post=get_post(pid)
    if not post.author_id==v.id:
        abort(403)

    post.is_deleted=True
    post.is_pinned=False
    post.stickied=False
    
    g.db.add(post)

    #clear cache
    cache.delete_memoized(User.userpagelisting, v, sort="new")
    cache.delete_memoized(Board.idlist, post.board)

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
            g.db.add(post)
            
    
        

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

    if not post.author_id==v.id and not v.admin_level>=3 and not post.board.has_mod(v):
        abort(403)

    if post.board.over_18 and post.over_18:
        abort(403)

    post.over_18 = not post.over_18
    g.db.add(post)
    

    return "", 204

@app.route("/api/toggle_post_nsfl/<pid>", methods=["POST"])
@is_not_banned
@validate_formkey
def toggle_post_nsfl(pid, v):

    post=get_post(pid)

    if not post.author_id==v.id and not v.admin_level>=3 and not post.board.has_mod(v):
        abort(403)

    if post.board.is_nsfl and post.is_nsfl:
        abort(403)

    post.is_nsfl = not post.is_nsfl
    g.db.add(post)
    

    return "", 204
