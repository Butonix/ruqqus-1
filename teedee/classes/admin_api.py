from flask import *
from teedee.classes import *
from teedee.helpers.wrappers import *
from secrets import token_hex
from teedee.__main__ import db, app

@app.route("/api/ban_user/<user_id>", methods=["POST"])
@admin_level_required(3)
@validate_formkey
def ban_user(user_id, v):

    user=db.query(User).filter_by(id=user_id).first()

    if not user:
        abort(400)

    user.is_banned=True

    db.add(user)
    db.commit()

@app.route("/api/unban_user/<user_id>", methods=["POST"])
@admin_level_required(3)
@validate_formkey
def ban_user(user_id, v):

    user=db.query(User).filter_by(id=user_id).first()

    if not user:
        abort(400)

    user.is_banned=False

    db.add(user)
    db.commit()
