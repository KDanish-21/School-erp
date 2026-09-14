# Little Scholars ERP — Railway deployment

Fully self-contained single-container image: Frappe + ERPNext + Education +
MariaDB + Redis, all running together in ONE Railway service via supervisord.
No separate database/cache services, no cross-service variable wiring —
adapted from the official [frappe_docker](https://github.com/frappe/frappe_docker)
(MIT licensed) "custom apps" pattern, then consolidated further than
frappe_docker's own multi-container split.

Built and verified end-to-end locally before being written up here: a fresh
container creates the site from scratch (frappe → erpnext → education),
**automatically seeds the full Little Scholars Public School demo** (120
students, 12 instructors, 4 weeks of attendance, mixed paid/overdue fees, a
graded mid-term exam, role-scoped users for every persona, and the navy/
marigold desk branding), serves real logins over HTTP, and — critically —
**persists correctly across a restart** (confirmed: restarting does NOT
re-initialize the database, recreate the site, or re-run the demo seed — it
goes straight to `bench migrate` and starts serving, exactly matching the
local dev bench).

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

Takes several minutes the first time — this is doing a lot of work in one
shot: initializes MariaDB's data directory, bootstraps a working root
password (see "MariaDB root auth" below for why this needs a specific
approach), creates the site and installs `erpnext` + `education`, then
**automatically runs the full demo seed** (`seed_school.py` +
`ui_polish.py`, baked into the image at `/home/frappe/`) — same scripts,
same data, as the local dev bench. A marker file
(`sites/<SITE_NAME>/.demo_seeded`) prevents this from ever re-running once
it succeeds, so every restart after that just runs `bench migrate` and
starts serving — confirmed by testing an actual restart.

**No manual steps required.** The moment the deploy finishes and you log in
as `Administrator` (the password you set via `ADMIN_PASSWORD`), you get the
exact same 120-student school — same roles, same fee/attendance/exam data,
same navy-and-marigold branding — as the local bench. Nothing to
restore, nothing to re-run by hand.

If you ever do need to re-seed from scratch (e.g. testing on a fresh
volume), the two scripts are idempotent and safe to re-run manually:
```bash
cd sites && ../env/bin/python /home/frappe/seed_school.py && ../env/bin/python /home/frappe/ui_polish.py
```

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
- **A site created headlessly via `bench new-site` skips several fixtures
  that ERPNext's *interactive* setup wizard normally installs first** —
  discovered one at a time, each blocking a later step of the demo seed:
  - `Company` creation failed on `Could not find Warehouse Type: Transit`
    — fixed by calling ERPNext's real
    `erpnext.setup.setup_wizard.operations.install_fixtures.install()` +
    `install_company()` instead of hand-rolling Company creation.
  - Student creation failed on `Could not find Gender: Male` — fixed by
    also calling Frappe's own
    `frappe.desk.page.setup_wizard.install_fixtures.install()` first.
  - Fee invoicing failed on `Could not find Default Price List: Standard
    Selling` — fixed by also calling `install_defaults(args)` from the
    same ERPNext fixtures module (creates the Standard Selling/Buying
    Price Lists + Global Defaults).
  - The branding script failed on `MandatoryError: language, time_zone`
    when saving `System Settings` — fixed by setting sensible India
    defaults (`en` / `Asia/Kolkata`) before save, since the wizard step
    that normally sets these never ran.
  
  All four are exercised by calling the *exact same wizard code path* a
  real interactive setup runs, rather than re-implementing a subset by
  hand — confirmed via two full fresh-volume boots and a restart-
  persistence check.

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
