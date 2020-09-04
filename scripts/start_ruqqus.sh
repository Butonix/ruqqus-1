pip3 install -r requirements.txt
export PATH=$PATH:~/ruqqus/ruqqus
cd ~
source ruqqus_configs.sh
cd ~/ruqqus/ruqqus
newrelic-admin run-program gunicorn __main__:app --daemon -k gevent -w $WEB_CONCURRENCY --worker-connections $WORKER_CONNECTIONS --max-requests 10000 --max-requests-jitter 500 --preload