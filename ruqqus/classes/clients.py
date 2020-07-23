from flask import *

from ruqqus.__main__ import app, Base

class OauthClient(Base):

	__tablename__="oauth_apps"

	id=Column(Integer, primary_key=True)
	client_id=Column(String(64))
	client_secret=Column(String(128))
	app_name=Column(String(50))
	redirect_uri=Column(String(4096))
	author_id=Column(Integer, ForeignKey("users.id"))


class ClientAuth(Base):

	__tablename__="client_auths"

	id=Column(Integer, primary_key=True)
	oauth_client=Column(Integer, ForeignKey("oauth_apps.id"))
	oauth_code=Column(String(128))
	user_id=Column(Integer, ForeignKey("users.id"))
	scope_identity=Column(Boolean, default=False)
	scope_create=Column(Boolean, default=False)
	scope_read=Column(Boolean, default=False)
	scope_update=Column(Boolean, default=False)
	scope_delete=Column(Boolean, default=False)
	scope_vote=Column(Boolean, default=False)
	scope_guildmaster=Column(Boolean, default=False)
	access_token=Column(String(128))
	refresh_token=Column(String(128))
	access_token_expire_utc=Column(Integer)