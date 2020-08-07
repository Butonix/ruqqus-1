from urllib.parse import urlparse
from time import time
import secrets

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.get import *
from ruqqus.classes import *
from flask import *
from ruqqus.__main__ import app

SCOPES={
    'identity':'See your username',
    'create':'Save posts and comments as you',
    'read':'View Ruqqus as you, including private or restricted content',
    'update':'Edit your posts and comments',
    'delete':'Delete your posts and comments',
    'vote':'Cast votes as you',
    'guildmaster':'Perform Guildmaster actions'
}


@app.route("/oauth/authorize", methods=["GET"])
@auth_required
def oauth_authorize_prompt(v):


    '''
    This page takes the following URL parameters:
    * client_id - Your application client ID
    * scope - Comma-separated list of scopes. Scopes are described above
    * redirect_uri - Your redirect link
    '''

    client_id=request.args.get("client_id")

    application= get_application(client_id)
    if not application:
        return jsonify({"oauth_error":"Invalid `client_id`"}), 401

    if application.is_banned:
        return jsonify({"oauth_error":"Banned `client_id`"}), 403
        
    scopes_txt = request.args.get('scope', "")

    scopes=scopes_txt.split(',')
    if not scopes:
        return jsonify({"oauth_error":"One or more scopes must be specified as a comma-separated list."}), 400

    for scope in scopes:
        if scope not in SCOPES:
            return jsonify({"oauth_error":f"The provided scope `{scope}` is not valid."}), 400


    redirect_uri = request.args.get("redirect_uri")
    if not redirect_uri:
        return jsonify({"oauth_error":f"`redirect_uri` must be provided."}), 400

    if not redirect_uri.startswith('https://') and not redirect_uri.startswith("https://localhost/"):
        return jsonify({"oauth_error":"redirect_uri must use https, or be localhost"}), 400


    valid_redirect_uris = [x.lstrip().rstrip() for x in application.redirect_uri.split(",")]

    if redirect_uri not in valid_redirect_uris:
        return jsonify({"oauth_error":"Invalid redirect_uri"}), 400

    state = request.args.get("state")
    if not state:
        return jsonify({'oauth_error':'state argument required'}), 400

    permanent = bool(request.args.get("permanent"))

    return render_template("oauth.html",
        v=v,
        application=application,
        SCOPES=SCOPES,
        state=state,
        scopes=scopes,
        scopes_txt=scopes_txt,
        redirect_uri=redirect_uri,
        permanent=int(permanent),
        i=random_image()
        )


@app.route("/oauth/authorize", methods=["POST"])
@auth_required
@validate_formkey
def oauth_authorize_post(v):

    client_id=request.form.get("client_id")
    scopes_txt=request.form.get("scopes")
    state=request.form.get("state")
    redirect_uri = request.form.get("redirect_uri")

    application = get_application(client_id)
    if not application:
        abort(404)
    if application.is_banned:
        abort(403)

    valid_redirect_uris = [x.lstrip().rstrip() for x in application.redirect_uri.split(",")]
    if redirect_uri not in valid_redirect_uris:
        return jsonify({"oauth_error":"Invalid redirect_uri"}), 400

    scopes=scopes_txt.split(',')
    if not scopes:
        return jsonify({"oauth_error":"One or more scopes must be specified as a comma-separated list"}), 400

    for scope in scopes:
        if scope not in SCOPES:
            return jsonify({"oauth_error":f"The provided scope `{scope}` is not valid."}), 400

    if not state:
        return jsonify({'oauth_error':'state argument required'}), 400

    permanent=bool(int(request.values.get("permanent",0)))


    new_auth=ClientAuth(
        oauth_client=application.id,
        oauth_code=secrets.token_urlsafe(128)[0:128],
        user_id=v.id,
        scope_identity="identity" in scopes,
        scope_create="create" in scopes,
        scope_read="read" in scopes,
        scope_update="update" in scopes,
        scope_delete="delete" in scopes,
        scope_vote = "vote" in scopes,
        scope_guildmaster="guildmaster" in scopes,
        refresh_token=secrets.token_urlsafe(128)[0:128] if permanent else None
        )

    g.db.add(new_auth)

    return redirect(f"{redirect_uri}?code={new_auth.oauth_code}&scopes={scopes_txt}&state={state}")


@app.route("/oauth/grant", methods=["post"])
def oauth_grant():

    '''
    This endpoint takes the following parameters:
    * code - The code parameter provided in the redirect
    * client_id - Your client ID
    * client_secret - your client secret
    '''


    application = get_application(request.values.get("client_id"))

    if not application or (request.values.get("client_secret") != application.client_secret):
        return jsonify({"oauth_error":"Invalid client ID or secret"}), 401

    if application.client_id != request.values.get("client_id"):
        return jsonify({"oauth_error":"Invalid client ID or secret"}), 401


    if request.values.get("grant_type")=="code":

        code=request.values.get("code")

        auth=g.db.query(ClientAuth).filter_by(oauth_code=code).first()

        if not auth:
            return jsonify({"oauth_error":"Invalid code"}), 401

        auth.oauth_code=None
        auth.access_token=secrets.token_urlsafe(128)[0:128]
        auth.access_token_expire_utc = int(time.time())+60*60

        g.db.add(auth)

        g.db.commit()

        data = {
            "access_token":auth.access_token,
            "scopes": auth.scopelist,
            "expires_at": auth.access_token_expire_utc,
            "token_type":"Bearer"
        }

        if auth.refresh_token:
            data["refresh_token"]= auth.refresh_token

        return jsonify(data)

    elif request.values.get("grant_type")=="refresh":

        auth=g.db.query(ClientAuth).filter_by(refresh_token=request.values.get("refresh_token")).first()

        auth.access_token=secrets.token_urlsafe(128)[0:128]
        auth.access_token_expire_utc = int(time.time())+60*60

        g.db.add(auth)

        data={
            "access_token":auth.access_token, 
            "expires_at": auth.access_token_expire_utc
        }

        return jsonify(data)

    else:
        return jsonify({"oauth_error":"Invalid grant type"})






@app.route("/api/v1/identity")
@api("identity")
def api_v1_identity(v):

    return jsonify(v.json)