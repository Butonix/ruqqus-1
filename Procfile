web: newrelic-admin run-program gunicorn ruqqus.__main__:app -w 4 -k gevent --worker-connections 5 --preload --max-requests 5000 --max-requests-jitter 250
worker: python3.7 scripts/recomputes.py
