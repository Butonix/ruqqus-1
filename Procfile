web: newrelic-admin run-program gunicorn ruqqus.__main__:app -w 2 -k gevent --worker-connections 6 --preload --max-requests 500 --max-requests-jitter 50
worker: python3.7 scripts/recomputes.py
