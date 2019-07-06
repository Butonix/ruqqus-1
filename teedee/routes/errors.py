from teedee.__main__ import app
from teedee.helpers.wrappers import *
from flask import *

#Errors
@auth_desired
def error_401(e, v=None):
    return render_template('401.html', v=v), 401

@auth_desired
def error_403(e, v=None):
    return render_template('403.html'), 403

@auth_desired
def error_404(e, v=None):
    return render_template('404.html'), 404

@auth_desired
def error_405(e, v=None):
    return render_template('405.html'), 405

@auth_desired
def error_500(e, v=None):
    return render_template('500.html', e=e, v=v), 500

app.register_error_handler(401, error_401)
app.register_error_handler(403, error_403)
app.register_error_handler(404, error_404)
app.register_error_handler(405, error_405)
app.register_error_handler(500, error_500)
