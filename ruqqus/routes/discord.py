from ruqqus.classes import *
from ruqqus.__main__ import app, db

@app.route("/discord_redirect")
@auth_required
def discord_redirect(v):

	code=request.args.get("code")
	if not code:
		abort(400)

