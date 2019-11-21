from ruqqus.helpers.wrappers import *
from flask import *
from ruqqus.__main__ import app

#Errors
@app.errorhandler(401)
@auth_desired
def error_401(e, v):
    return render_template('errors/401.html', v=v), 401

@app.errorhandler(403)
@auth_desired
def error_403(e, v):
    return render_template('errors/403.html', v=v), 403

@app.errorhandler(404)
@auth_desired
def error_404(e, v):
    return render_template('errors/404.html', v=v), 404

@app.errorhandler(405)
@auth_desired
def error_405(e, v):
    return render_template('errors/405.html', v=v), 405

@app.errorhandler(429)
@auth_desired
def error_405(e, v):
    return render_template('errors/429.html', v=v), 429

@app.errorhandler(500)
@auth_desired
def error_500(e, v):
    return render_template('errors/500.html', e=e, v=v), 500
