cd ~
source ruqqus_configs.sh
cd ~/ruqqus
newrelic-admin run-program gunicorn ruqqus.__main__:app --daemon -k gevent -w $WEB_CONCURRENCY --worker-connections $WORKER_CONNECTIONS --max-requests 10000 --max-requests-jitter 500 --preload