class PaymentRequired(Exception):
    status_code=402
    def __init__(self):
        Exception.__init__(self)
        self.status_code=402

@app.errorhandler(PaymentRequired)
@auth_desired
@api()
def error_402(e, v):
    return{"html": lambda: (render_template('errors/402.html', v=v), 402),
           "api": lambda: (jsonify({"error": "402 Payment Required"}), 402)
           }
