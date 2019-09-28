
FROM ubuntu:18.04

MAINTAINER "Keiron O'Shea <keo7@aber.ac.uk>"

RUN apt-get update && apt-get install \
  -y --no-install-recommends curl python3 python3-virtualenv

RUN curl -sL https://deb.nodesource.com/setup_6.x | bash - \
    && apt-get install -y nodejs npm

ADD ./ /limbus

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m virtualenv --python=/usr/bin/python3 $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ENV FLASK_CONFIG=dev
ENV FLASK_APP=run.py
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

WORKDIR /limbus

RUN pip install -r /limbus/requirements.txt
RUN npm install yarn -g
RUN yarn install
CMD ["python", "/limbus/limbus/run.py"]