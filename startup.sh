cd ~
sudo cp ruqqus/nginx.txt /etc/nginx/sites-available/ruqqus.com.conf
sudo nginx -s reload
source venv/bin/activate
source env.sh
cd ~/ruqqus
pip3 install -r requirements.txt
export domain=ruqqus.com
export PYTHONPATH=$PYTHONPATH:~/ruqqus
export CACHE_TYPE=filesystem
export CACHE_DIR=cachetemp
export S3_BUCKET_NAME=i.ruqqus.com
export HCAPTCHA_SITEKEY=22beca86-6e93-421c-8510-f07c6914dadb
cd ~
NEW_RELIC_CONFIG_FILE=newrelic.ini
newrelic-admin run-program gunicorn ruqqus.__main__:app -k gevent -w $WEB_CONCURRENCY --worker-connections $WORKER_CONNECTIONS --max-requests 10000 --max-requests-jitter 500 --preload --bind 127.0.0.1:5000
deactivate