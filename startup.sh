echo "startup script running"
python3.7 ruqqus/helpers/db_prep.py
echo "database functions set"
echo "starting server"
gunicorn ruqqus.__main__:app -w 2 -k gevent --worker-connections 9