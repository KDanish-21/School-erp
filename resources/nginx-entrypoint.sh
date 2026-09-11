#!/bin/bash
# Adapted from frappe_docker's resources/core/nginx/nginx-entrypoint.sh (MIT licensed,
# https://github.com/frappe/frappe_docker) — only change is LISTEN_PORT, so this
# container can bind to Railway's dynamic $PORT instead of a hardcoded 8080.
set -e

if [[ -z "$BACKEND" ]]; then
  export BACKEND=0.0.0.0:8000
fi
if [[ -z "$SOCKETIO" ]]; then
  export SOCKETIO=0.0.0.0:9000
fi
if [[ -z "$UPSTREAM_REAL_IP_ADDRESS" ]]; then
  export UPSTREAM_REAL_IP_ADDRESS=127.0.0.1
fi
if [[ -z "$UPSTREAM_REAL_IP_HEADER" ]]; then
  export UPSTREAM_REAL_IP_HEADER=X-Forwarded-For
fi
if [[ -z "$UPSTREAM_REAL_IP_RECURSIVE" ]]; then
  export UPSTREAM_REAL_IP_RECURSIVE=off
fi
if [[ -z "$FRAPPE_SITE_NAME_HEADER" ]]; then
  # shellcheck disable=SC2016
  export FRAPPE_SITE_NAME_HEADER='$host'
fi
if [[ -z "$PROXY_READ_TIMEOUT" ]]; then
  export PROXY_READ_TIMEOUT=120
fi
if [[ -z "$CLIENT_MAX_BODY_SIZE" ]]; then
  export CLIENT_MAX_BODY_SIZE=50m
fi
# Railway injects $PORT with the port it routes public traffic to; fall back to 8080 locally.
export LISTEN_PORT="${PORT:-8080}"

# shellcheck disable=SC2016
envsubst '${BACKEND}
  ${SOCKETIO}
  ${UPSTREAM_REAL_IP_ADDRESS}
  ${UPSTREAM_REAL_IP_HEADER}
  ${UPSTREAM_REAL_IP_RECURSIVE}
  ${FRAPPE_SITE_NAME_HEADER}
  ${PROXY_READ_TIMEOUT}
  ${CLIENT_MAX_BODY_SIZE}
  ${LISTEN_PORT}' \
  </templates/nginx/frappe.conf.template >/etc/nginx/conf.d/frappe.conf

exec nginx -g 'daemon off;'
