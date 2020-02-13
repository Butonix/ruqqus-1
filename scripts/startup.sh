python3.7 scripts/recomputes.py
gunicorn ruqqus.__main__:app -w 3 -k gevent --worker-connections 6