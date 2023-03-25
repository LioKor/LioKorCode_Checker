FROM ubuntu:22.04

WORKDIR /root/liokor_code_checker
COPY . .

RUN apt update
RUN apt install apt-transport-https ca-certificates curl software-properties-common python3 python3-pip -y
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
RUN add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu jammy stable"
RUN apt install docker-ce -y
RUN pip3 install -r requirements/prod.txt
RUN cp config.template.py config.py

EXPOSE 8080

CMD uwsgi uwsgi.ini
