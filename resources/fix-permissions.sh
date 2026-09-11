#!/bin/bash
# Runs once at container start, as root (supervisord's default user, before
# any per-program `user=frappe` drop). A freshly-attached Railway Volume
# mounts as an empty root-owned directory — nothing else in this image can
# write to it until it's chowned. Also links the baked (image-layer) desk
# assets into the sites volume, same as frappe_docker's own main-entrypoint.sh.
set -e

mkdir -p /var/lib/mysql /var/run/mysqld
chown -R frappe:frappe /var/lib/mysql /var/run/mysqld
chown -R frappe:frappe /home/frappe/frappe-bench/sites /home/frappe/frappe-bench/logs

ASSETS_PATH="/home/frappe/frappe-bench/sites/assets"
BAKED_PATH="/home/frappe/frappe-bench/assets"
rm -rf "$ASSETS_PATH"
ln -s "$BAKED_PATH" "$ASSETS_PATH"
chown -h frappe:frappe "$ASSETS_PATH"

exit 0
