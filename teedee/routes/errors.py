from teedee.helpers.wrappers import *
from flask import *
from teedee.__main__ import app

#Errors
@app.errorhandler(401)
@auth_desired
def error_401(e, v=None):
    return render_template('401.html', v=v), 401

@app.errorhandler(403)
@auth_desired
def error_403(e, v=None):
    return render_template('403.html'), 403

@app.errorhandler(404)
@auth_desired
def error_404(e, v=None):
    return render_template('404.html'), 404

@app.errorhandler(405)
@auth_desired
def error_405(e, v=None):
    return render_template('405.html'), 405

@app.errorhandler(500)
@auth_desired
def error_500(e, v=None):
    return render_template('500.html', e=e, v=v), 500
