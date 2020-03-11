web: newrelic-admin run-program gunicorn ruqqus.__main__:app -w 3 -k gevent --worker-connections 6 --preload --max-requests 10000 --max-requests-jitter 500
worker: python3.7 scripts/recomputes.py
