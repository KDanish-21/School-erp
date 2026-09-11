#!/bin/bash
# Runs as the frappe user (supervisord's `user=frappe` for this program).
#
# On first boot (empty /var/lib/mysql, a fresh Railway Volume): initializes
# the data directory, then bootstraps root access via a temporary
# --skip-grant-tables instance. This is necessary because
# `mariadb-install-db --auth-root-authentication-method=normal` does NOT
# reliably avoid unix_socket auth for root — confirmed by testing: root ended
# up on unix_socket, which only permits the OS user literally named "root" to
# authenticate (we run as "frappe"), so every bench connection was denied
# regardless of password. --skip-grant-tables sidesteps this entirely: it
# disables auth-plugin checking altogether, letting us set a real password
# unconditionally, the same bulletproof recipe used to reset a lost MySQL/
# MariaDB root password.
set -e

DATADIR=/var/lib/mysql
SOCK=/var/run/mysqld/mysqld.sock
ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-changeit123}"

if [ ! -d "$DATADIR/mysql" ]; then
  echo "==> Initializing MariaDB data directory (first boot)"
  mariadb-install-db --datadir="$DATADIR" --auth-root-authentication-method=normal

  echo "==> Bootstrapping root password via a temporary --skip-grant-tables instance"
  /usr/sbin/mariadbd --datadir="$DATADIR" --socket="$SOCK" --skip-grant-tables --skip-networking &
  TEMP_PID=$!
  for i in $(seq 1 30); do [ -S "$SOCK" ] && break; sleep 1; done

  # IDENTIFIED VIA mysql_native_password (not bare IDENTIFIED BY) is required —
  # confirmed by direct testing: a plain "IDENTIFIED BY" on an account whose
  # CURRENT plugin is unix_socket does not actually switch the plugin away
  # from it, so password-based connections keep getting rejected even though
  # a password was "set". Explicitly naming the plugin forces the switch.
  mariadb --socket="$SOCK" -e "
    FLUSH PRIVILEGES;
    ALTER USER 'root'@'localhost' IDENTIFIED VIA mysql_native_password USING PASSWORD('${ROOT_PASSWORD}');
    CREATE USER IF NOT EXISTS 'root'@'127.0.0.1' IDENTIFIED VIA mysql_native_password USING PASSWORD('${ROOT_PASSWORD}');
    GRANT ALL PRIVILEGES ON *.* TO 'root'@'127.0.0.1' WITH GRANT OPTION;
    FLUSH PRIVILEGES;
  "

  kill "$TEMP_PID"
  wait "$TEMP_PID" 2>/dev/null || true
  echo "==> Root password bootstrap complete"
fi

exec /usr/sbin/mariadbd \
  --datadir="$DATADIR" \
  --socket="$SOCK" \
  --bind-address=127.0.0.1 \
  --port=3306 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci
