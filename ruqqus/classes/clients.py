from flask import *
from sqlalchemy import *
from sqlalchemy.orm import relationship

from .mix_ins import Stndrd
from ruqqus.__main__ import app, Base

class OauthApp(Base, Stndrd):

	__tablename__="oauth_apps"

	id=Column(Integer, primary_key=True)
	client_id=Column(String(64))
	client_secret=Column(String(128))
	app_name=Column(String(50))
	redirect_uri=Column(String(4096))
	author_id=Column(Integer, ForeignKey("users.id"))
	is_banned=Column(Boolean, default=False)
	description=Column(String(256), default=None)

	author=relationship("User")

	def __repr__(self):
		return f"<OauthApp(id={self.id})>"

	@property
	def permalink(self):

		return f"/admin/app/{self.base36id}"


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

	user=relationship("User", lazy="joined")
	application = relationship("OauthApp", lazy="joined")

	@property
	def scopelist(self):

		output=""
		output += "identity," if self.scope_identity else ""
		output += "create," if self.scope_create else ""
		output += "read," if self.scope_read else ""
		output += "update," if self.scope_update else ""
		output += "delete," if self.scope_delete else ""
		output += "vote," if self.scope_vote else ""
		output += "guildmaster," if self.scope_guildmaster else ""

		output=output.rstrip(',')

		return output