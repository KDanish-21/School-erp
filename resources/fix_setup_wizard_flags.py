"""
Closes the last headless-`bench new-site` gap: even after Company/Fiscal
Year/Price Lists are created directly (see seed_school.py's
setup_company_and_fiscal_year), Frappe still thinks the interactive setup
wizard was never *finished*, because nothing ever set the handful of flags
the wizard's own completion step (disable_future_access() in
frappe/desk/page/setup_wizard/setup_wizard.py) sets:

  - Installed Application.is_setup_complete for frappe + erpnext
  - the "desktop:home_page" global default (defaults to "setup-wizard")
  - System Settings.setup_complete

Symptom without this fix: logging in as Administrator (or any System
Manager) redirects to /desk/setup-wizard/0 instead of the desk, and once
Installed Application flags get fixed without also fixing the home_page
default, the desk gets stuck in an infinite reload loop — router.js's
`frappe.re_route["setup-wizard"] = "app"` fights with add_home_page()
sending it back to "setup-wizard" every time. Confirmed the hard way on
the live Railway deployment.

Deliberately run on EVERY boot (not gated by the .demo_seeded marker) —
cheap, idempotent, and this is the same category of "always run" fixup as
`bench migrate` in bootstrap.sh, not a one-time seed step.
"""
import os

import frappe

SITE_NAME = os.environ.get("SITE_NAME", "erp.localhost")
SITES_PATH = os.environ.get("SITES_PATH", "/Users/danishkhan/frappe-bench/sites")

frappe.init(site=SITE_NAME, sites_path=SITES_PATH)
frappe.connect()
frappe.set_user("Administrator")


def log(msg):
    print(f"[fixup] {msg}")


def run():
    changed = False

    for app_name in ("frappe", "erpnext"):
        if not frappe.db.get_value("Installed Application", {"app_name": app_name}, "is_setup_complete"):
            frappe.db.set_value("Installed Application", {"app_name": app_name}, "is_setup_complete", 1)
            changed = True

    if frappe.db.get_default("desktop:home_page") != "workspace":
        frappe.db.set_default("desktop:home_page", "workspace")
        changed = True

    if not frappe.db.get_single_value("System Settings", "setup_complete"):
        frappe.db.set_single_value("System Settings", "setup_complete", frappe.is_setup_complete())
        changed = True

    if changed:
        frappe.clear_cache()
        frappe.db.commit()
        log("setup-wizard completion flags fixed")
    else:
        log("setup-wizard completion flags already OK")


if __name__ == "__main__":
    run()
    frappe.db.commit()
