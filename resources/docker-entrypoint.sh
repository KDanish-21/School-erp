#!/bin/bash
# Combined entrypoint for the single-container Railway deployment.
# Runs once per container start: link baked assets, wait for the managed
# MariaDB/Redis services, write site config, create the site on first boot
# (idempotent — safe on every restart), then hand off to supervisord which
# runs nginx/gunicorn/socketio/worker/scheduler together.
set -e

BENCH_DIR=/home/frappe/frappe-bench
# SITE_NAME must equal the exact public domain this app will be reached at
# (Railway's generated *.up.railway.app domain, or your custom domain).
# nginx routes requests to /<Host-header>/public/... on disk, so the site's
# own directory name has to match whatever hostname visitors actually use —
# there's no safe generic default here, unlike ADMIN_PASSWORD.
: "${SITE_NAME:?SITE_NAME env var is required — set it to the exact domain this app is served at (e.g. your-app.up.railway.app)}"

echo "==> Linking baked assets into the sites volume"
rm -rf "$BENCH_DIR/sites/assets"
ln -s "$BENCH_DIR/assets" "$BENCH_DIR/sites/assets"

cd "$BENCH_DIR"

echo "==> Waiting for MariaDB at ${MYSQLHOST}:${MYSQLPORT}"
wait-for-it -t 120 "${MYSQLHOST}:${MYSQLPORT}"

echo "==> Waiting for Redis at ${REDISHOST}:${REDISPORT}"
wait-for-it -t 120 "${REDISHOST}:${REDISPORT}"

echo "==> Writing common site config"
bench set-config -g db_host "$MYSQLHOST"
bench set-config -gp db_port "$MYSQLPORT"
# One Railway Redis instance serves cache + queue + socketio (separate key
# prefixes inside frappe keep them from colliding) — cheaper than three.
bench set-config -g redis_cache "$REDIS_URL"
bench set-config -g redis_queue "$REDIS_URL"
bench set-config -g redis_socketio "$REDIS_URL"
bench set-config -gp socketio_port 9000
bench set-config -g chromium_path /usr/bin/chromium-headless-shell
bench set-config -g serve_default_site true

if [ ! -d "sites/$SITE_NAME" ]; then
  echo "==> Site $SITE_NAME not found — creating it"
  bench new-site "$SITE_NAME" \
    --db-host "$MYSQLHOST" \
    --db-port "$MYSQLPORT" \
    --db-root-username "$MYSQLUSER" \
    --db-root-password "$MYSQLPASSWORD" \
    --admin-password "${ADMIN_PASSWORD:?ADMIN_PASSWORD env var is required on first boot}" \
    --install-app erpnext \
    --install-app education \
    --set-default
else
  echo "==> Site $SITE_NAME already exists — running migrations"
  bench --site "$SITE_NAME" migrate
fi

echo "==> Starting supervisord (nginx, gunicorn, socketio, worker, scheduler)"
exec supervisord -c /etc/supervisor/conf.d/supervisord.conf
