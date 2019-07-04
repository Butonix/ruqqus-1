from teedee.creds.credentials import *
from flask import Flask


app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{0}:{1}@127.0.0.1/{2}?host=127.0.0.1?port={3}/charset=utf8/' \
                                        ''.format(DBUNAME, DBPASS, DB, DBPORT)


