from ruqqus.__main__ import app, db
from ruqqus.classes import *

@app.route("/discord_redirect")
@auth_required
def discord_redirect(v):

	code=request.args.get("code")
	if not code:
		abort(400)

