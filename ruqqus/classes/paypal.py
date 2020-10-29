import requests
from os import environ
import time
from sqlalchemy import *
from sqlalchemy.orm import relationship, deferred

from ruqqus.__main__ import Base

PAYPAL_ID=environ.get("PAYPAL_CLIENT_ID", "").rstrip()
PAYPAL_SECRET=environ.get("PAYPAL_CLIENT_SECRET", "").rstrip()

PAYPAL_URL="https://api.paypal.com"

class PayPalClient():

	def __init__(self):

		self.paypal_token=None
		self.token_expires=0

	def print(self, x):

		try:
			print(x)
		except OSError:
			pass

	def new_token(self):

		url=f"{PAYPAL_URL}/v1/oauth2/token"

		headers={
			"Accept":"application/json"
		}

		data={
			"grant_type":"client_credentials"
		}

		x=requests.post(url, headers=headers, data=data, auth=(PAYPAL_ID,PAYPAL_SECRET))

		x=x.json()

		self.paypal_token=x["access_token"]
		self.token_expires=int(time.time())+int(x["expires_in"])

	def _get(self, url):

		if time.time()>self.token_expires:
			self.new_token()

		url=PAYPAL_URL+url

		headers={
			"Content-Type":"application/json",
		#	"Accept":"application/json",
			"Authorization":f"Bearer {self.paypal_token}"
			}

		return requests.get(url, headers=headers)


	def _post(self, url, data=None):

		if time.time()>self.token_expires:
			self.new_token()

		url=PAYPAL_URL+url

		headers={
			"Content-Type":"application/json",
		#	"Accept":"application/json",
			"Authorization":f"Bearer {self.paypal_token}"
			}
		self.print(url)
		self.print(headers)
		self.print(data)

		return requests.post(url, headers=headers, json=data)

	def create(self, txn):

		url="/v2/checkout/orders"

		data={
			"intent":"CAPTURE",
			"purchase_units":
			[
				{
				"amount": {
					"currency_code":"USD",
					"value": str(txn.usd_cents/100)
					}
				}
			]
		}

		r=self._post(url, data=data)

		x=r.json()

		if x["status"]=="CREATED":
			txn.paypal_id=x["id"]
			txn.status=1

	def authorize(self, txn):

		url=f"{txn.paypal_url}/authorize"

		x= self._post(url)
		x=x.json()

		status=x["status"]
		if status in ["SAVED", "COMPLETED"]:
			txn.status=2

		return x["status"] in ["SAVED", "COMPLETED"]


	def capture(self, txn):

		url=f"{txn.paypal_url}/capture"

		x=self._post(url)
		x=x.json()
		
		status=x["status"]
		if status=="COMPLETED":
			txn.status=3

		return status=="COMPLETED"


class PayPalTxn(Base):

	__tablename__="paypal_txns"

	id=Column(Integer, primary_key=True)
	user_id=Column(Integer, ForeignKey("users.id"))
	created_utc=Column(Integer)
	paypal_id=Column(String)
	usd_cents=Column(Integer)
	coin_count=Column(Integer)

	status=Column(Integer, default=0) #0=initialized 1=created, 2=authorized, 3=captured, -1=failed, -2=reversed 

	user=relationship("User", lazy="dynamic")

	@property
	def approve_url(self):

		return f"https://www.paypal.com/checkoutnow?token={self.paypal_id}"

	@property
	def paypal_url(self):

		return f"/v2/checkout/orders/{self.paypal_id}"