#!/bin/bash
# One-shot setup, runs as the frappe user after mariadb+redis are reachable:
# bench site config, first-boot site creation (or migrate on every later
# restart). Root's password is already bootstrapped by start-mariadb.sh by
# the time this runs. Exits when done — not a long-running program
# (supervisord.conf sets autorestart=false for this one).
set -e

BENCH_DIR=/home/frappe/frappe-bench
SITE_NAME="${SITE_NAME:?SITE_NAME env var is required — set it to the exact domain this app is served at (e.g. your-app.up.railway.app)}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-changeit123}"

cd "$BENCH_DIR"

echo "==> Waiting for local MariaDB"
wait-for-it -t 60 127.0.0.1:3306
echo "==> Waiting for local Redis"
wait-for-it -t 60 127.0.0.1:6379

echo "==> Writing common site config"
bench set-config -g db_host 127.0.0.1
bench set-config -gp db_port 3306
bench set-config -g redis_cache "redis://127.0.0.1:6379"
bench set-config -g redis_queue "redis://127.0.0.1:6379"
bench set-config -g redis_socketio "redis://127.0.0.1:6379"
bench set-config -gp socketio_port 9000
bench set-config -g chromium_path /usr/bin/chromium-headless-shell
bench set-config -g serve_default_site true

if [ ! -d "sites/$SITE_NAME" ]; then
  echo "==> Site $SITE_NAME not found — creating it"
  bench new-site "$SITE_NAME" \
    --db-host 127.0.0.1 \
    --db-port 3306 \
    --db-root-username root \
    --db-root-password "$MYSQL_ROOT_PASSWORD" \
    --admin-password "${ADMIN_PASSWORD:?ADMIN_PASSWORD env var is required on first boot}" \
    --install-app erpnext \
    --install-app education \
    --set-default
else
  echo "==> Site $SITE_NAME already exists — running migrations"
  bench --site "$SITE_NAME" migrate
fi

echo "==> Bootstrap complete"
