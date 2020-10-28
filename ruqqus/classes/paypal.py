import requests
from os import environ
import time
from sqlalchemy import *
from sqlalchemy.orm import relationship, deferred

from ruqqus.__main__ import Base

PAYPAL_ID=environ.get("PAYPAL_CLIENT_ID", "").rstrip()
PAYPAL_SECRET=environ.get("PAYPAL_CLIENT_SECRET", "").rstrip()

PAYPAL_URL="https://api.paypal.com"

def paypal_get(url, data):

	url=PAYPAL_URL+url

	headers={"Content-Type":"application/json"}

	return requests.get(url, headers=headers, data=data)


def paypal_post(url, data):

	url=PAYPAL_URL+url

	headers={"Content-Type":"application/json"}

	return requests.post(url, headers=headers, data=data)

class PayPal(Base):

	__tablename__="paypal"

	id=Column(Integer, primary_key=True)
	user_id=Column(Integer, ForeignKey("users.id"))
	created_utc=Column(Integer)
	paypal_id=Column(String)
	usd_cents=Column(Integer)

	status=Column(Integer, default=1) #1=created, 2=authorized, 3=captured, -1=failed, -2=reversed  

	def __init__(self, *args, **kwargs):

		super().__init__(*args, **kwargs)

		self.create()

	def create(self):

		url="/v2/checkouts/orders"

		data={
			"intent":"CAPTURE",
			"purchase_units":
			[
				"amount": {
					"currency_code":"USD",
					"value": str(self.usd_cents/100)
				}
			]
		}

		r=paypal_post(url, data=data)

		x=r.json()

		if x["status"]=="CREATED":
			self.paypal_id=x["id"]


	def authorize(self):

		url=f"{self.paypal_url}/authorize"

		paypal_post(url)


	def capture(self):

		url=f"{self.paypal_url}/capture"

		paypal_post(url)

	@property
	def approve_url(self):

		return f"https://www.paypal.com/checkoutnow?token={self.paypal_id}"

	@property
	def paypal_url(self):

		return f"{PAYPAL_URL}/v2/checkout/orders/{self.paypal_id}"