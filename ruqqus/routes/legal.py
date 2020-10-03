from flask import *
from os import environ
import requests
from werkzeug.utils import secure_filename
import mistletoe

from ruqqus.helpers.get import *
from ruqqus.helpers.wrappers import *
from ruqqus.helpers.markdown import CustomRenderer
from ruqqus.helpers.sanitize import *
from ruqqus.mail.mail import send_mail
from ruqqus.__main__ import app, limiter

@app.route("/legal", methods=["GET"])
@auth_desired
def legal_1(v):
    return render_template("legal/legal.html", v=v)

@app.route("/legal/2", methods=["POST"])
@is_not_banned
@validate_formkey
def legal_2(v):

    if request.form.get("username") != v.username:
        abort(422)

    if request.form.get("about_yourself","") not in ["law_enforcement","gov_official"]:
        return render_template("legal/legal_reject.html", v=v)

    req_type=request.form.get("request_type","")

    if req_type=="user_info_baseless":
        return render_template("legal/legal_reject2.html", v=v)
    elif req_type=="user_info_emergency":
        return render_template("legal/legal_emergency.html", v=v)
    elif req_type=="post_takedown":
        return render_template("legal/legal_takedown.html", v=v)
    elif req_type=="user_info_legal":
        return render_template("legal/legal_user.html", v=v)
    elif req_type=="data_save":
        return render_template("legal/legal_infosave.html", v=v)
    else:
        abort(400)


@app.route("/legal/final", methods=["POST"])
@is_not_banned
@validate_formkey
def legal_final(v):

    if request.form.get("username") != v.username:
        abort(422)

    data=[(x, request.form[x]) for x in request.form if x !="formkey"]

    data=sorted(data, key=lambda x: x[0])

    files={secure_filename(request.files[x].filename): request.files[x] for x in request.files}

    try:
        send_mail(environ.get("admin_email"),
              "Legal request submission",
              render_template("email/legal.html",
                                     data=data),
              files=files
              )
    except:
            return render_template("legal/legal_done.html",
                           success=False,
                           v=v)

    return render_template("legal/legal_done.html",
                           success=True,
                           v=v)

@app.route("/help/dmca", methods=["POST"])
@is_not_banned
@validate_formkey
def dmca_post(v):

    data={x: request.form[x] for x in request.form if x !="formkey"}

    email_text=render_template("help/dmca_email.md", v=v, **data)

    with CustomRenderer() as renderer:
        email_html=renderer.render(mistletoe.Document(email_text))
    email_html=sanitize(email_md, linkgen=True)
    
    try:
        send_mail(environ.get("admin_email"),
              "DMCA Takedown Request",
              email_html
              )
    except:
        return render_template("/help/dmca.html",
                           error="Unable to save your request. Please try again later.",
                           v=v)

    post_text=render_template("help/dmca_notice.md", v=v, **data)
    with CustomRenderer() as renderer:
        post_html=renderer.render(mistletoe.Document(post_text))
    post_html=sanitize(post_md, linkgen=True)

    #create +RuqqusDMCA post
    new_post=Submission(author_id=1,
                        domain_ref=None,
                        board_id=1000,
                        original_board_id=1000,
                        over_18=False,
                        post_public=True,
                        repost_id=None,
                        is_offensive=False
                        )

    g.db.add(new_post)
    g.db.flush()

    new_post_aux=SubmissionAux(id=new_post.id,
                               url=None,
                               body=post_text,
                               body_html=post_html_html,
                               embed_url=None,
                               title=f"DMCA {new_post.base36id}"
                               )

    g.db.add(new_post_aux)
    g.db.commit()

    return render_template("/help/dmca.html",
                           msg="Your request has been saved.",
                           v=v)
    
@app.route("/help/counter_dmca", methods=["POST"])
@is_not_banned
@validate_formkey
def counter_dmca_post(v):

    data=[(x, request.form[x]) for x in request.form if x !="formkey"]
    data.append(("username", v.username))
    data.append(("email", v.email))

    data=sorted(data, key=lambda x: x[0])
    try:
        send_mail(environ.get("admin_email"),
              "DMCA Counter Notice",
              render_template("email/counter_dmca.html",
                                     data=data),
                  plaintext=str(data)
              )
    except:
            return render_template("/help/counter_dmca.html",
                           error="Unable to save your request. Please try again later.",
                           v=v)

    return render_template("/help/counter_dmca.html",
                           msg="Your request has been saved.",
                           v=v)
