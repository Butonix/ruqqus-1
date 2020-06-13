web: newrelic-admin run-program gunicorn ruqqus.__main__:app -w 5 -k gevent --worker-connections 1 --preload --max-requests 5000 --max-requests-jitter 250
worker: python3.7 scripts/recomputes.py
