\#!/bin/sh
cd ~/
source venv/bin/activate
source env.sh
cd ~/ruqqus/scripts
export PYTHONPATH=$PYTHONPATH:~/ruqqus
python mailing_list.py
deactivate