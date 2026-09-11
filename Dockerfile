# Little Scholars Public School — fully self-contained single-container image
# for Railway: Frappe + ERPNext + Education + MariaDB + Redis all in one.
#
# Adapted from the official frappe_docker "custom" image
# (https://github.com/frappe/frappe_docker, MIT licensed). Deliberate
# differences from the upstream pattern:
#   1. apps.json is COPYed directly instead of passed as a BuildKit --secret —
#      our apps (frappe/erpnext/education) are all public repos, so there is
#      nothing in apps.json worth keeping out of image history.
#   2. MariaDB and Redis are installed IN this image and run locally
#      (127.0.0.1) under supervisord, instead of being separate Railway
#      services — this is a single-service deployment: no cross-service
#      variable wiring, just SITE_NAME + ADMIN_PASSWORD and two volumes.
#   3. supervisord runs nginx + gunicorn + socketio + worker + scheduler +
#      mariadb + redis together in ONE container/process group.

ARG PYTHON_VERSION=3.14
ARG DEBIAN_BASE=bookworm
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_BASE} AS base

ARG WKHTMLTOPDF_VERSION=0.12.6.1-3
ARG WKHTMLTOPDF_DISTRO=bookworm
ARG INSTALL_CHROMIUM=true
ARG NODE_VERSION=24
ENV NVM_DIR=/home/frappe/.nvm
ENV NVM_SYMLINK_CURRENT=true
ENV PATH=${NVM_DIR}/current/bin/:${PATH}

RUN useradd -ms /bin/bash frappe \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
    curl git vim nginx gettext-base file supervisor \
    libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 libpangocairo-1.0-0 \
    restic gpg \
    mariadb-server mariadb-client redis-server less \
    wait-for-it jq media-types \
    && mkdir -p ${NVM_DIR} \
    && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.6/install.sh | bash \
    && . ${NVM_DIR}/nvm.sh \
    && nvm install ${NODE_VERSION} \
    && nvm use ${NODE_VERSION} \
    && npm install -g yarn \
    && corepack enable pnpm \
    && nvm alias default ${NODE_VERSION} \
    && rm -rf ${NVM_DIR}/.cache \
    && if [ "$(uname -m)" = "aarch64" ]; then export ARCH=arm64; fi \
    && if [ "$(uname -m)" = "x86_64" ]; then export ARCH=amd64; fi \
    && downloaded_file=wkhtmltox_${WKHTMLTOPDF_VERSION}.${WKHTMLTOPDF_DISTRO}_${ARCH}.deb \
    && curl -sLO https://github.com/wkhtmltopdf/packaging/releases/download/$WKHTMLTOPDF_VERSION/$downloaded_file \
    && apt-get install -y ./$downloaded_file \
    && rm $downloaded_file \
    && if [ "$INSTALL_CHROMIUM" != "false" ]; then \
        DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y chromium-headless-shell; \
    fi \
    && rm -rf /var/lib/apt/lists/* \
    # Debian's mariadb-server postinst auto-runs its own mariadb-install-db
    # during `apt-get install`, baking a pre-initialized /var/lib/mysql (with
    # Debian's own unix_socket-only root setup) into this image layer. A
    # brand-new Docker/Railway Volume mounted over that path gets seeded from
    # the image's existing content on first use, which silently skips our own
    # start-mariadb.sh first-boot bootstrap entirely (it only initializes when
    # the directory is empty). Wipe it here so the image's own copy is empty,
    # guaranteeing our script's first-boot logic is what actually runs.
    && rm -rf /var/lib/mysql/* \
    && rm -fr /etc/nginx/sites-enabled/default \
    && mkdir -p /etc/nginx/snippets \
    && pip3 install frappe-bench \
    && sed -i '/user www-data/d' /etc/nginx/nginx.conf \
    && touch /run/nginx.pid \
    && chown -R frappe:frappe /etc/nginx/conf.d /etc/nginx/nginx.conf /etc/nginx/snippets \
    && chown -R frappe:frappe /var/log/nginx /var/lib/nginx /run/nginx.pid

COPY resources/nginx-template.conf /templates/nginx/frappe.conf.template
COPY resources/nginx-entrypoint.sh /usr/local/bin/nginx-entrypoint.sh
COPY resources/security_headers.conf /etc/nginx/snippets/security_headers.conf
RUN chmod 755 /usr/local/bin/nginx-entrypoint.sh

FROM base AS builder

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    wget libpq-dev libffi-dev liblcms2-dev libldap2-dev libmariadb-dev libsasl2-dev \
    libtiff5-dev libwebp-dev pkg-config redis-tools rlwrap tk8.6-dev cron gcc \
    build-essential libbz2-dev \
    && rm -rf /var/lib/apt/lists/*

USER frappe

ARG FRAPPE_BRANCH=develop
ARG FRAPPE_PATH=https://github.com/frappe/frappe

COPY --chown=frappe:frappe apps.json /home/frappe/apps.json

RUN bench init \
  --apps_path=/home/frappe/apps.json \
  --frappe-branch=${FRAPPE_BRANCH} \
  --frappe-path=${FRAPPE_PATH} \
  --python=python3 \
  --no-procfile \
  --no-backups \
  --skip-redis-config-generation \
  --verbose \
  /home/frappe/frappe-bench && \
  cd /home/frappe/frappe-bench && \
  echo "{}" > sites/common_site_config.json && \
  find apps -mindepth 1 -path "*/.git" | xargs rm -fr

FROM base AS erpnext

USER frappe

COPY --from=builder --chown=frappe:frappe /home/frappe/frappe-bench /home/frappe/frappe-bench

WORKDIR /home/frappe/frappe-bench

RUN cp -r /home/frappe/frappe-bench/sites/assets /home/frappe/frappe-bench/assets && \
  rm -rf /home/frappe/frappe-bench/sites/assets

# No Dockerfile VOLUME instruction here — Railway's builder rejects it
# ("use Railway Volumes" instead). Attach Railway Volumes at
# /home/frappe/frappe-bench/sites AND /var/lib/mysql in the service's
# Settings → Volumes; the container works the same either way, this only
# affects `docker run` defaults for local testing.

USER root
COPY resources/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY resources/fix-permissions.sh /usr/local/bin/fix-permissions.sh
COPY resources/start-mariadb.sh /usr/local/bin/start-mariadb.sh
COPY resources/bootstrap.sh /usr/local/bin/bootstrap.sh
RUN chmod 755 /usr/local/bin/fix-permissions.sh /usr/local/bin/start-mariadb.sh /usr/local/bin/bootstrap.sh \
  && mkdir -p /home/frappe/frappe-bench/config/pids /var/lib/mysql /var/run/mysqld \
  && chown -R frappe:frappe /home/frappe/frappe-bench/config

ENV GUNICORN_THREADS=2
ENV GUNICORN_WORKERS=1
ENV GUNICORN_TIMEOUT=120

# Stays root: supervisord itself runs as root (needed to fix up freshly-
# mounted Railway Volumes' ownership at startup), then drops each individual
# program to the non-root `frappe` user via supervisord.conf's `user=` directive.
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
