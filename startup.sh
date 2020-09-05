cd ~
sudo cp ruqqus/nginx.txt /etc/nginx/sites-available/aws.ruqqus.com.conf
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
cd ~
gunicorn ruqqus.__main__:app -k gevent -w $WEB_CONCURRENCY --worker-connections $WORKER_CONNECTIONS --max-requests 10000 --max-requests-jitter 500 --preload --bind 127.0.0.1:5000
deactivate