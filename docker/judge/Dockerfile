FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    HOME=/tmp \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        g++ \
        openjdk-21-jdk-headless \
        nodejs \
        python3 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 65532 judge \
    && useradd \
        --uid 65532 \
        --gid 65532 \
        --no-create-home \
        --home-dir /tmp \
        --shell /usr/sbin/nologin \
        judge \
    && install -d -o root -g root -m 0755 /opt/judge

COPY --chown=root:root runner.py /opt/judge/runner.py

ENTRYPOINT ["python3", "/opt/judge/runner.py"]
