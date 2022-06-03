FROM alpine

RUN echo "@testing http://nl.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories
RUN apk update

RUN apk add bash make python3 gcc g++ gfortran go nasm lua nodejs fpc@testing
#RUN apk add clang-extra-tools

#RUN apk add py3-pip
#RUN pip install pylint

#RUN apk add npm
#RUN npm install -g eslint