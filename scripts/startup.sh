python3.7 ruqqus/helpers/db_prep.py
gunicorn ruqqus.__main__:app -w 2 -k gevent --worker-connections 9