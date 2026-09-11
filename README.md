# Little Scholars ERP — Railway deployment

Single-container Frappe + ERPNext + Education image, built for Railway. Adapted
from the official [frappe_docker](https://github.com/frappe/frappe_docker)
(MIT licensed) "custom apps" pattern, consolidated into one container running
nginx + gunicorn + socketio + a background worker + the scheduler together
(via supervisord) instead of frappe_docker's usual one-container-per-process
split — cheaper to run as a single Railway service.

## What you need in Railway (one project, 3 services)

1. **MariaDB** — add from Railway's template gallery ("MariaDB" or the
   community MySQL-compatible template).
2. **Redis** — add from Railway's template gallery.
3. **This app** — "New Web Service" → connect this GitHub repo. Railway will
   detect `railway.json` and build `Dockerfile` automatically.

## Required environment variables on the app service

Set these under the app service's **Variables** tab. Railway reference syntax
(`${{ServiceName.VAR}}`) pulls values from the other two services automatically
— no copy-pasting credentials:

| Variable | Value |
|---|---|
| `MYSQLHOST` | `${{MariaDB.MYSQLHOST}}` |
| `MYSQLPORT` | `${{MariaDB.MYSQLPORT}}` |
| `MYSQLUSER` | `${{MariaDB.MYSQLUSER}}` |
| `MYSQLPASSWORD` | `${{MariaDB.MYSQLPASSWORD}}` |
| `REDISHOST` | `${{Redis.REDISHOST}}` |
| `REDISPORT` | `${{Redis.REDISPORT}}` |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` |
| `ADMIN_PASSWORD` | pick a real password — used once, on first boot, to set the site's Administrator password |
| `SITE_NAME` | **required** — must exactly match the public domain this app is served at (generate the domain in Networking first, see below) |

(Adjust the service names in `${{...}}` to whatever you actually name the
MariaDB/Redis services in your Railway project — Railway autocompletes these
in the dashboard's variable editor.)

## ⚠️ Attach a persistent volume — do this before the first deploy

The image declares `/home/frappe/frappe-bench/sites` and `.../logs` as Docker
volumes, but **without an actual persistent volume attached in Railway, every
redeploy wipes the site and recreates it from scratch** (confirmed locally —
recreating the container without a named volume loses the whole site,
students and all). In the app service: **Settings → Volumes → New Volume**,
mount it at `/home/frappe/frappe-bench/sites`. Do this *before* the first
deploy, or your first-boot site creation will need to happen again after you
add it.

## Networking

In the app service's **Settings → Networking**, generate a public domain (or
add your own later). Railway sets `$PORT` automatically; nginx inside the
container listens on it.

## First boot

On first start, the entrypoint (`resources/docker-entrypoint.sh`) creates the
site fresh (`bench new-site` + installs `erpnext` and `education`) — this
takes a few minutes the very first time. Every subsequent restart just runs
`bench migrate` and starts serving, since the site already exists in the
`sites` volume.

**This gives you a fresh, empty Education install** — not the exact demo data
from the local dev bench (120 students, fees, attendance, branding, etc.).
That data lives in MariaDB and the site's `files` folder, not in this repo, so
it doesn't come along automatically. To bring it over:

```bash
# On the local dev machine — takes a full backup (db + public + private files)
cd ~/frappe-bench
bench --site erp.localhost backup --with-files

# Copy the resulting sites/erp.localhost/private/backups/*.sql.gz,
# *-files.tar, *-private-files.tar to the Railway container (e.g. via
# `railway run bash` and scp/curl, or a temporary object storage link), then:

bench --site erp.production --force restore <timestamp>-database.sql.gz \
  --with-public-files <timestamp>-files.tar \
  --with-private-files <timestamp>-private-files.tar \
  --db-root-username "$MYSQLUSER" --db-root-password "$MYSQLPASSWORD"
```

Alternatively — since the demo data was built entirely by two idempotent
scripts (`seed_school.py`, `ui_polish.py`) rather than by hand — you can just
run those two scripts against the fresh Railway site instead of restoring a
binary backup. They reproduce the exact same 120 students / fees / attendance
/ branding from scratch. This needs the Company + Chart of Accounts that the
setup wizard normally creates interactively; ask for a scripted version of
that step if you go this route.

## Debugging on Railway

`railway run bash` (or the Railway dashboard's shell) drops you into the
container. Check process status with:
```bash
supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status
```

## Local test build

```bash
docker build -f Dockerfile -t lsps-erp:test .
```
