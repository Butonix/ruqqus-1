cd ~/ruqqus
pip3 install -r requirements.txt
export PYTHONPATH=$PYTHONPATH:~/ruqqus
export CACHE_TYPE=filesystem
cd ~
source env.sh
newrelic-admin run-program gunicorn ruqqus.__main__:app -k gevent -w $WEB_CONCURRENCY --worker-connections $WORKER_CONNECTIONS --max-requests 10000 --max-requests-jitter 500 --preload --bind 0.0.0.0:8000