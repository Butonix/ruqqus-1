FROM heroku/heroku:18

COPY supervisord.conf /etc/supervisord.conf

RUN apt update \
    && apt install -y supervisor \
    && apt install -y python3.7 \
    && apt install -y python3-pip

RUN mkdir -p /opt/ruqqus/service

COPY requirements.txt /opt/ruqqus/service/requirements.txt

RUN cd /opt/ruqqus/service \
    && pip3 install -r requirements.txt
    
EXPOSE 8000/tcp

CMD [ "/usr/bin/supervisord", "-c", "/etc/supervisord.conf" ]
