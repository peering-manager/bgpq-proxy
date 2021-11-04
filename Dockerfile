FROM python:3.9-alpine AS builder

RUN mkdir app && \
    apk add --no-cache build-base autoconf automake gcc git linux-headers musl-dev

WORKDIR /app
COPY . /app 

RUN pip install -U pip wheel && \
    pip install -U -r requirements.txt && \
    pip install 'uwsgi>=2.0,<2.1'

FROM builder AS bgpq3_builder

WORKDIR /bgp3

RUN mkdir /bgpq3 && \
    git clone https://github.com/snar/bgpq3 . && git checkout v0.1.36 && \
    ./configure && make install 

FROM builder AS bgpq4_builder

WORKDIR /bgp4

RUN mkdir /bgpq4 && \
    git clone https://github.com/bgp/bgpq4.git . && git checkout 0.0.7 && \
    ./bootstrap && ./configure && make install 

FROM python:3.9-alpine

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.9 /usr/local/lib/python3.9
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/bgpqproxy /app/bgpqproxy
COPY --from=bgpq3_builder /usr/local/bin/bgpq3 /usr/local/bin
COPY --from=bgpq4_builder /usr/local/bin/bgpq4 /usr/local/bin

EXPOSE 5000

CMD [ \
    "uwsgi", \
    "--uid", "nobody", \
    "--http-socket", "0.0.0.0:5000", \
    "--manage-script-name", "--wsgi", "bgpqproxy:create_app()", \
    "--threads", "10", "--processes", "10", "--thunder-lock" \
    ]
