# Little Scholars ERP — Railway deployment

Fully self-contained single-container image: Frappe + ERPNext + Education +
MariaDB + Redis, all running together in ONE Railway service via supervisord.
No separate database/cache services, no cross-service variable wiring —
adapted from the official [frappe_docker](https://github.com/frappe/frappe_docker)
(MIT licensed) "custom apps" pattern, then consolidated further than
frappe_docker's own multi-container split.

Built and verified end-to-end locally before being written up here: a fresh
container creates the site from scratch (frappe → erpnext → education),
serves real logins over HTTP, and — critically — **persists correctly across
a restart** (confirmed: restarting does NOT re-initialize the database or
recreate the site, it goes straight to `bench migrate` and starts serving).

## What you need in Railway — just this one service

**No MariaDB or Redis services to add.** Just:

1. In Railway: **New Web Service** → connect this GitHub repo (`KDanish-21/School-erp`).
   Railway will detect `railway.json` and build `Dockerfile` automatically.
2. **Two volumes**, attached *before* the first deploy (Settings → Volumes → New Volume):
   - mount path `/home/frappe/frappe-bench/sites`
   - mount path `/var/lib/mysql`

   Both are required for persistence. Without them, a redeploy wipes
   everything and rebuilds the site from scratch — confirmed by testing.
   (Redis has no persistent volume — it's just cache + job queue here, fine
   to lose on restart, no real data lives there.)
3. **Networking**: Settings → Networking → Generate Domain. Note the exact
   domain it gives you (e.g. `school-erp-production.up.railway.app`).
4. **Variables** — only two are actually required:

| Variable | Value |
|---|---|
| `SITE_NAME` | **must exactly match** the domain from step 3 — nginx routes by that hostname, so a mismatch breaks the desk UI's assets even though the API still responds |
| `ADMIN_PASSWORD` | pick a real password — sets the site's Administrator login on first boot |

Optional:

| Variable | Default if unset |
|---|---|
| `MYSQL_ROOT_PASSWORD` | `changeit123` — internal only, MariaDB binds to `127.0.0.1` inside the container, never reachable from outside it |

That's it. No `MYSQLHOST`/`REDISHOST`/etc. — MariaDB and Redis both run
locally in this same container.

## First boot

Takes a few minutes the first time: initializes MariaDB's data directory,
bootstraps a working root password (see "MariaDB root auth" below for why
this needs a specific approach), then creates the site and installs
`erpnext` + `education`. Every restart after that just runs `bench migrate`
and starts serving — confirmed by testing an actual restart.

**This gives you a fresh, empty Education install** — not the exact demo
data from the local dev bench (120 students, fees, attendance, branding).
That data lives in the database/files, not in this repo. To bring it over,
either restore a real `bench backup --with-files` from the local bench, or
re-run the two idempotent scripts (`seed_school.py`, `ui_polish.py`) against
this site — they reproduce the same data from scratch. Ask for a scripted
version of the Company/Chart-of-Accounts step (normally done via the
interactive setup wizard) if you go this route.

## Notable things fixed while building this (for future reference)

- **No Dockerfile `VOLUME` instruction** — Railway's builder rejects it
  outright ("use Railway Volumes instead"). Persistence works the same via
  the two Railway Volumes above; nothing in the image needs to declare it.
- **`Containerfile` had to be renamed to `Dockerfile`** — Railway only
  auto-detects that exact filename for its Docker builder, even with
  `railway.json` specifying `dockerfilePath` explicitly.
- **nginx can't symlink its error log to `/dev/stderr`** under this
  root-supervisord-then-setuid-to-frappe process model — the child's fresh
  `open()` of that path gets `EACCES` even though it can freely write to its
  own already-inherited stderr fd. Fixed by letting nginx use plain regular
  log files instead of the symlink trick.
- **MariaDB root auth needs the bulletproof `--skip-grant-tables` reset**,
  not `mariadb-install-db --auth-root-authentication-method=normal` alone —
  that flag did not reliably avoid `unix_socket` auth on root, which then
  refuses every connection from a non-`root` OS user (we run as `frappe`).
  Also needs `IDENTIFIED VIA mysql_native_password` explicitly, not a bare
  `IDENTIFIED BY` — the latter doesn't actually switch the auth plugin away
  from `unix_socket` on an existing account.
- **Debian's `mariadb-server` package auto-initializes `/var/lib/mysql`
  during `apt-get install`**, baking that into the image layer. A brand-new
  Railway Volume mounted over that path gets seeded from the image's
  existing content on first use — silently skipping this image's own
  first-boot bootstrap logic entirely. Fixed by wiping `/var/lib/mysql` at
  the end of the image build so the volume always starts genuinely empty.

## Debugging on Railway

`railway run bash` (or the dashboard's shell) drops you into the container.
```bash
supervisorctl -c /etc/supervisor/conf.d/supervisord.conf status
```

## Local test build

```bash
docker build -f Dockerfile -t lsps-erp:test .
docker volume create test-sites && docker volume create test-mysql
docker run -d -p 8080:8080 \
  -v test-sites:/home/frappe/frappe-bench/sites \
  -v test-mysql:/var/lib/mysql \
  -e SITE_NAME=erp.localtest -e ADMIN_PASSWORD=admin -e PORT=8080 \
  lsps-erp:test
```
