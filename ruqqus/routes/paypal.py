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

def coins_to_price_cents(n):

    if n>=52:
        return 100*n - 1001
    elif n>=26:
        return 100*n-401
    elif n>=12:
        return 100*n-101
    elif n >=4:
        return 100*n-1
    else:
        return 100*n+49

@app.route("/shop/get_price", methods=["GET"])
def shop_get_price():

    coins=int(request.args.get("coins"))

    return jsonify({"price":coins_to_price_cents(coins)/100})


@app.route("/shop/buy_coins", methods=["POST"])
@is_not_banned
def shop_buy_coins(v):

    coin_count=int(request.form.get("coin_count",1))

    new_txn=PayPalTxn(
        user_id=v.id,
        created_utc=int(time.time()),
        coin_count=coin_count,
        usd_cents=coins_to_price_cents(coin_count)
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

    if not CLIENT.capture(txn):
        abort(402)

    g.db.add(txn)
    g.db.flush()

    #successful payment - award coins

    v.coin_balance += txn.coin_count

    g.db.add(v)

    return redirect("/settings/premium")
