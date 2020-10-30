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
@no_negative_balance("html")
@validate_formkey
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


@app.route("/shop/negative_balance", methods=["POST"])
@is_not_banned
@validate_formkey
def shop_negative_balance(v):

    new_txn=PayPalTxn(
        user_id=v.id,
        created_utc=int(time.time()),
        coin_count=None,
        usd_cents=v.negative_balance_cents
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

    if txn.coin_count:
        v.coin_balance += txn.coin_count
    else:
        v.negative_balance_cents -= txn.usd_cents

    g.db.add(v)

    return redirect("/settings/premium")

@app.route("/shop/paypal_webhook")
def paypal_webhook_handler():
    print(request.path)
    print(request.method)

    data=request.get_json()
    pprint.pprint(data)
    
    #Reversals
    if data["event_type"] in ["PAYMENT.SALE.REVERSED", "PAYMENT.SALE.REFUNDED"]:

        txn=get_txn(data["resource"]["id"])

        amount_cents=int(float(data["resource"]["amount"]["total"])*100)

    elif data["event_type"] in ["PAYMENT.CAPTURE.REVERSED", "PAYMENT.CAPTURE.REFUNDED"]:

        txn=get_txn(data["resource"]["id"])

        amount_cents=int(float(data["resource"]["amount"]["value"])*100)

    txn.user.negative_balance_cents+=amount_cents

    txn.status=-2

    g.db.add(txn)
    g.db.add(txn.user)

    g.db.flush()



    return "", 204