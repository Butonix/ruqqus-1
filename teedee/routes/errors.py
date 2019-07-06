from teedee.__main__ import app

#Errors
@app.errorhandler(401)
def error_401(e):
    return render_template('401.html'), 401

@app.errorhandler(403)
def error_403(e):
    return render_template('403.html'), 403

@app.errorhandler(404)
def error_404(e):
    return render_template('404.html'), 404

@app.errorhandler(405)
def error_405(e):
    return render_template('405.html'), 405

@app.errorhandler(500)
def error_500(e):
    return render_template('500.html', e=e), 500
