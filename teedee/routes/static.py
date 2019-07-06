from teedee.__main__ import app

#take care of static pages
@app.route('/static/<path:path>')
def static_service(path):
    return send_from_directory('./static', path)
