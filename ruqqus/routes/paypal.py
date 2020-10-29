from os import environ
import requests
import urllib
import hmac
import pprint
import time

from flask import *

from ruqqus.classes import *
from ruqqus.helpers.wrappers import *
from ruqqus.helpers.security import *
from ruqqus.__main__ import app

CLIENT=PayPalClient()


@app.route("/shop/buy_coins", methods=["POST"])
@is_not_banned
def shop_buy_coins(v):

    coin_count=int(request.form.get("coin_count",1))

    new_txn=PayPalTxn(
        user_id=v.id,
        created_utc=int(time.time()),
        usd_cents=100*coin_count-1
        )

    CLIENT.create(new_txn)

    g.db.add(new_txn)
    g.db.commit()

    return redirect(new_txn.approve_url)


@app.route("/shop/buy_coins_completed", methods=["GET"])
@is_not_banned
def shop_buy_coins_completed(v):

    #look up most recent txn
    txn=g.db.query(PayPalTxn).filter_by(user_id=v.id, status=1).first()

    if not txn:
        abort(400)

    if not CLIENT.authorize(txn):
        abort(402)

    if not CLIENT.capture(txn):
        abort(402)

    #successful payment - award coins
    coins=int(usd_cents+1)

    v.coin_balance += coins

    g.db.add(v)

    return redirect("/settings/profile#ruqqus-premium")
