from ruqqus.__main__ import *
from ruqqus.classes import User

from ruqqus.helpers.discord import *

@app.route("/discord_redirect")
@auth_required
def discord_redirect(v):

	code=request.args.get("code")
	if not code:
		abort(400)

	