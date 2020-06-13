web: newrelic-admin run-program gunicorn ruqqus.__main__:app -w 4 -k gevent --worker-connections 4 --preload --max-requests 500 --max-requests-jitter 50
worker: python3.7 scripts/recomputes.py
