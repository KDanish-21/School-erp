"""
Single source of truth for ADRS Techno branding — imported by every seed/
polish/guide script instead of each one hand-duplicating the same name and
color constants. Confirmed live from https://adrstechno.com/: legal name,
tagline, and the real color palette (a near-black/graphite monochrome scale
with a recurring deep-navy undertone, #172554 — present directly in their
compiled CSS, not invented).
"""

import os

COMPANY_NAME = "ADRS Technology Private Limited"
COMPANY_ABBR = "ADRS"
BRAND_SHORT = "ADRS Techno"
BRAND_TAGLINE = "Innovation & Tech"

SCHOOL_NAME = "ADRS Academy"
SCHOOL_ABBR = "ADRSA"
SCHOOL_DOMAIN = "adrsacademy.in"

HOSPITAL_NAME = "ADRS Healthcare"
HOSPITAL_DOMAIN = "adrshealth.in"

# Old identity, kept only so the live-site migration script can find and
# rename what's already there.
OLD_COMPANY_NAME = "Danish"
OLD_SCHOOL_DOMAIN = "littlescholars.edu.in"
OLD_HOSPITAL_DOMAIN = "citycarehospital.in"

NAVY = "#172554"        # real ADRS deep-navy undertone
NAVY_DARK = "#0B1120"   # near-black navy, also present in their real palette
ACCENT = "#4D5565"      # muted slate — one shared accent for both modules
MUTED_ON_DARK = "#B8BDC9"  # ADRS's real --linear-text-muted — secondary text on navy, not ACCENT (too low-contrast there)
CHARCOAL = "#222326"    # ADRS's real light-surface text color
BG_LIGHT = "#F4F5F8"    # ADRS's real light-bg color
BORDER = "#DDE1EA"      # ADRS's real light-border color

LOGO_LIGHT_FILENAME = "adrs_logo.png"       # black wordmark, for light backgrounds
LOGO_DARK_FILENAME = "adrs_logo_dark.png"   # white wordmark, for dark backgrounds


def ensure_static_logo_file(filename: str) -> str:
    """Bundled real ADRS wordmark PNG (the Dockerfile COPYs it to
    /home/frappe/<filename> alongside this module; local dev runs copy it
    next to this file too) — saved into the site's own File storage so it
    gets a stable, servable URL. Idempotent (skips re-saving if a File with
    this name already exists), and self-contained here rather than in
    ui_polish.py specifically because bootstrap.sh runs the guide-page
    scripts *before* ui_polish.py on first boot — each caller needs to be
    able to ensure this file exists on its own, not assume another script
    already created it. Resolved relative to this module's own directory
    (not a hardcoded /home/frappe) so the exact same code works both in the
    container and against a local dev bench.
    """
    import frappe
    from frappe.utils.file_manager import save_file

    existing = frappe.db.get_value("File", {"file_name": filename}, "file_url")
    if existing:
        return existing
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    with open(local_path, "rb") as f:
        png_bytes = f.read()
    file_doc = save_file(filename, png_bytes, dt=None, dn=None, is_private=0, decode=False)
    return file_doc.file_url
