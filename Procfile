web: newrelic-admin run-program gunicorn ruqqus.__main__:app -w 3 -k gevent --worker-connections 6
worker: python3.7 scripts/recomputes.py
