FROM postgres:16

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential postgresql-server-dev-16 curl tar ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# pg_uuidv7 확장 프로그램
RUN cd /tmp && \
    curl -LO "https://github.com/fboulnois/pg_uuidv7/archive/refs/tags/v1.6.0.tar.gz" && \
    tar -xzf v1.6.0.tar.gz && \
    cd pg_uuidv7-1.6.0 && \
    make && make install

RUN rm -rf /tmp/pg_uuidv7-1.6.0 /tmp/v1.6.0.tar.gz
