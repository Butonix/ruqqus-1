from flask import *
from ruqqus.__main__ import app

class PaymentRequired(Exception):
    status_code=402
    def __init__(self):
        Exception.__init__(self)
        self.status_code=402
