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
    --install-app healthcare \
    --set-default
else
  echo "==> Site $SITE_NAME already exists — running migrations"
  bench --site "$SITE_NAME" migrate
fi

# Self-heal: a site created BEFORE healthcare was added to this deploy
# (i.e. the already-live site) goes through the `migrate` branch above,
# which does NOT install new apps — only `bench new-site` does that, and
# only on a brand-new site. Without this check, redeploying this exact
# code onto that existing site's volume would silently keep it on just
# erpnext+education forever.
if ! bench --site "$SITE_NAME" list-apps | grep -q "^healthcare"; then
  # `sites/apps.txt` — which app names a site is even ALLOWED to
  # install — lives in the mounted sites/ Volume, not the image. It's
  # written once at `bench init` time and never refreshed, so an
  # already-existing site's copy still only lists whatever apps existed
  # in apps.json the day it was first created. Adding a new app to
  # apps.json and rebuilding the image bakes its source into apps/ (image
  # layer) just fine, but `bench install-app` refuses to proceed with
  # "App healthcare not in apps.txt" until this file — the volume's copy —
  # also lists it. Confirmed the hard way on a simulated upgrade of an
  # existing site.
  if ! grep -qx "healthcare" sites/apps.txt; then
    echo "==> Registering healthcare in sites/apps.txt (new app since this site was created)"
    # apps.txt may not end in a newline (bench doesn't guarantee one), so a
    # naive `>>` append can glue onto the last line instead of starting a new
    # one (e.g. "erpnext" + "healthcare" -> "erpnexthealthcare"). Guard first.
    if [ -s sites/apps.txt ] && [ -n "$(tail -c1 sites/apps.txt)" ]; then
      echo >> sites/apps.txt
    fi
    echo "healthcare" >> sites/apps.txt
  fi
  echo "==> Installing healthcare app on existing site"
  bench --site "$SITE_NAME" install-app healthcare
fi

echo "==> Ensuring setup-wizard completion flags (idempotent, runs every boot)"
export SITE_NAME
export SITES_PATH="$BENCH_DIR/sites"
(cd "$SITES_PATH" && "$BENCH_DIR/env/bin/python" /home/frappe/fix_setup_wizard_flags.py)

echo "==> Ensuring the public guide pages are up to date (idempotent, runs every boot)"
# Version-checked against PAGE_VERSION inside each script, same reason as
# fix_setup_wizard_flags.py above: a content update needs to reach an
# already-seeded site on its next redeploy, not just a brand-new one.
(cd "$SITES_PATH" && "$BENCH_DIR/env/bin/python" /home/frappe/guide.py)
(cd "$SITES_PATH" && "$BENCH_DIR/env/bin/python" /home/frappe/school_guide.py)
(cd "$SITES_PATH" && "$BENCH_DIR/env/bin/python" /home/frappe/health_guide.py)

SEED_MARKER="sites/$SITE_NAME/.demo_seeded"
if [ ! -f "$SEED_MARKER" ]; then
  echo "==> Seeding demo data + branding (first time only for this site)"
  export SITE_NAME
  export SITES_PATH="$BENCH_DIR/sites"
  # All scripts do a raw frappe.init() (not via the `bench` CLI wrapper),
  # which needs cwd = sites/ for frappe's own logger to resolve its
  # "../logs" path correctly — confirmed the hard way earlier in this project.
  (cd "$SITES_PATH" && "$BENCH_DIR/env/bin/python" /home/frappe/seed_school.py)
  (cd "$SITES_PATH" && "$BENCH_DIR/env/bin/python" /home/frappe/ui_polish.py)
  touch "$SEED_MARKER"
  echo "==> Demo data + branding seeded"
else
  echo "==> Demo data already seeded — skipping"
fi

# Deliberately a SEPARATE marker from .demo_seeded: the school seed above
# already ran (and its marker already exists) on the live site by the time
# this was added, so gating hospital seeding on the SAME marker would skip
# it forever there.
HOSPITAL_SEED_MARKER="sites/$SITE_NAME/.hospital_seeded"
if [ ! -f "$HOSPITAL_SEED_MARKER" ]; then
  echo "==> Seeding hospital demo data + terminology (first time only for this site)"
  export SITE_NAME
  export SITES_PATH="$BENCH_DIR/sites"
  (cd "$SITES_PATH" && "$BENCH_DIR/env/bin/python" /home/frappe/seed_hospital.py)
  (cd "$SITES_PATH" && "$BENCH_DIR/env/bin/python" /home/frappe/polish_healthcare.py)
  touch "$HOSPITAL_SEED_MARKER"
  echo "==> Hospital demo data + terminology seeded"
else
  echo "==> Hospital demo data already seeded — skipping"
fi

echo "==> Bootstrap complete"
