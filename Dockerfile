FROM python:alpine

RUN apk add --no-cache --virtual .build-deps \
  gcc libxml2-dev libxslt-dev musl-dev linux-headers \
&& apk add --no-cache \
  wget \
  bash \
  curl \
  git \
  jq \
  libxml2 \
  libxslt \
  musl \
  zlib \
  openssh-client \
  zip \
  openjdk8-jre

COPY . /source

RUN wget https://bootstrap.pypa.io/get-pip.py --no-check-certificate \
  && python3 get-pip.py \
  && pip3 install -e /source

RUN apk del .build-deps
