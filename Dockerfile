FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
# gcc and python3.12-dev is needed only for uwsgi
RUN apt update && apt install curl software-properties-common gcc -y
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
RUN add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu jammy stable"
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt update && apt install docker-ce python3.12 python3.12-dev -y
RUN curl -sSL https://install.python-poetry.org | python3

WORKDIR /root/liokor_code_checker
COPY src ./src
COPY uwsgi.ini ./
COPY pyproject.toml ./
COPY poetry.toml ./
COPY poetry.lock ./
COPY config.template.py ./config.py

RUN /root/.local/share/pypoetry/venv/bin/poetry env use 3.12 && /root/.local/share/pypoetry/venv/bin/poetry install
RUN . ./.venv/bin/activate

EXPOSE 8080
CMD /root/liokor_code_checker/.venv/bin/uwsgi uwsgi.ini
