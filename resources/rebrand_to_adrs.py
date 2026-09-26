"""
One-time migration for a site that was seeded BEFORE the ADRS Techno
rebrand — renames the old fictional identity (Company "Danish", users on
littlescholars.edu.in / citycarehospital.in) to the new one. A brand-new
site never needs this: seed_school.py/seed_hospital.py already create
everything under the new identity from birth.

The rename steps are each a no-op once already done (checked against live
DB state, not a marker), so this is safe to run on every boot like guide.py
and fix_setup_wizard_flags.py. The branding-script rerun is the one part
gated behind an actual marker file (.adrs_branding_applied) rather than "did
a rename just happen" — see the comment on that check in run_all() for why.

Confirmed against the installed Frappe/ERPNext source before writing this
(not assumed): both Company and User have `allow_rename: 1`. Company's own
`after_rename` hook renames the docname, updates `company_name`, and fixes
DefaultValue rows — it does NOT touch `abbr` or any abbr-suffixed Account/
Cost Center names (e.g. "Cash - D" stays "Cash - D"), and cascading that
would mean bulk-renaming every default GL account for a purely cosmetic
internal suffix most demo viewers never see — deliberately left alone.
User's own `after_rename` hook cascades `owner`/`modified_by` audit columns,
and Frappe's generic rename engine separately cascades every Link-field
reference (Healthcare Practitioner.user_id, Student.user, etc.) on its own.

Run with:
    cd ~/frappe-bench/sites
    ../env/bin/python ../rebrand_to_adrs.py
"""
import os
import subprocess
import sys

import frappe

import brand

SITE_NAME = os.environ.get("SITE_NAME", "erp.localhost")
SITES_PATH = os.environ.get("SITES_PATH", "/Users/danishkhan/frappe-bench/sites")

frappe.init(site=SITE_NAME, sites_path=SITES_PATH)
frappe.connect()
frappe.set_user("Administrator")

OLD_DOMAINS = [brand.OLD_SCHOOL_DOMAIN, brand.OLD_HOSPITAL_DOMAIN]


def log(msg):
    print(f"[rebrand] {msg}")


def rename_company() -> bool:
    if not frappe.db.exists("Company", brand.OLD_COMPANY_NAME):
        return False
    if frappe.db.exists("Company", brand.COMPANY_NAME):
        log(f"Both '{brand.OLD_COMPANY_NAME}' and '{brand.COMPANY_NAME}' exist — skipping company rename")
        return False
    frappe.rename_doc("Company", brand.OLD_COMPANY_NAME, brand.COMPANY_NAME)
    log(f"Company '{brand.OLD_COMPANY_NAME}' -> '{brand.COMPANY_NAME}'")
    return True


def rename_users() -> bool:
    renamed = 0
    for old_domain in OLD_DOMAINS:
        old_emails = frappe.get_all(
            "User", filters={"name": ["like", f"%@{old_domain}"]}, pluck="name",
        )
        for old_email in old_emails:
            local_part = old_email.rsplit("@", 1)[0]
            new_domain = brand.SCHOOL_DOMAIN if old_domain == brand.OLD_SCHOOL_DOMAIN else brand.HOSPITAL_DOMAIN
            new_email = f"{local_part}@{new_domain}"
            if frappe.db.exists("User", new_email):
                continue
            frappe.rename_doc("User", old_email, new_email)
            renamed += 1
    if renamed:
        log(f"{renamed} user(s) renamed to new email domains")
    return renamed > 0


def rerun_branding_scripts():
    # Shelled out as separate processes (matching exactly how bootstrap.sh
    # invokes every other script) rather than imported in-process — both
    # scripts call frappe.init()/frappe.connect() at module import time, and
    # doing that a second time inside this already-connected process is an
    # unnecessary hazard to avoid for zero benefit. Resolved relative to
    # this module's own directory (matching brand.ensure_static_logo_file)
    # so the same code works both in the container and a local dev bench.
    here = os.path.dirname(os.path.abspath(__file__))
    for script in ("ui_polish.py", "polish_healthcare.py"):
        subprocess.run([sys.executable, os.path.join(here, script)], check=True, cwd=SITES_PATH)


BRANDING_MARKER = os.path.join(SITES_PATH, SITE_NAME, ".adrs_branding_applied")


def run_all():
    company_changed = rename_company()
    frappe.db.commit()
    users_changed = rename_users()
    frappe.db.commit()

    if not company_changed and not users_changed:
        log("Nothing to rename")

    # A persistent marker, not just "did a rename just happen": gating on
    # the rename outcome alone has a real failure mode, hit while testing
    # this exact script — if rerun_branding_scripts() itself fails partway
    # (e.g. a workspace save choking on stale data from an unrelated
    # upstream app upgrade), the rename step already committed, so a retry
    # sees nothing left to rename and would silently skip branding forever,
    # leaving the site's Company/emails migrated but its logo/colors/
    # workspace titles stuck on the old identity indefinitely. The marker
    # is only written after rerun_branding_scripts() succeeds, so a retry
    # after a partial failure tries branding again regardless of whether
    # any renaming is left to do.
    if not os.path.exists(BRANDING_MARKER):
        rerun_branding_scripts()
        open(BRANDING_MARKER, "w").close()
    else:
        log("Branding already applied")

    frappe.clear_cache()
    log("Done.")


if __name__ == "__main__":
    run_all()
    frappe.db.commit()
