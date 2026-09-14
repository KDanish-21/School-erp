"""
Desk branding + workspace polish for "Little Scholars Public School".
Run AFTER seed_school.py. Same idempotent-ORM-script pattern.

Run with:
    cd ~/frappe-bench/sites
    ../env/bin/python ../ui_polish.py
"""
import io
import os

import frappe
from PIL import Image, ImageDraw, ImageFont

SITE_NAME = os.environ.get("SITE_NAME", "erp.localhost")
SITES_PATH = os.environ.get("SITES_PATH", "/Users/danishkhan/frappe-bench/sites")

frappe.init(site=SITE_NAME, sites_path=SITES_PATH)
frappe.connect()
frappe.set_user("Administrator")

SCHOOL_NAME = "Little Scholars Public School"
NAVY = "#1B3B6F"
NAVY_DARK = "#12294D"
MARIGOLD = "#F2A93B"
CHARCOAL = "#4A5568"
PARCHMENT = "#FDF8F0"

# macOS path first (local dev reruns), Debian/Railway container path second.
_FONT_CANDIDATES_BOLD = [
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_BOLD = next((p for p in _FONT_CANDIDATES_BOLD if os.path.exists(p)), None)
if FONT_BOLD is None:
    raise RuntimeError(
        "No bold serif font found for the crest logo — checked: "
        + ", ".join(_FONT_CANDIDATES_BOLD)
    )


def log(msg):
    print(f"[ui] {msg}")


# ---------------------------------------------------------------- 1. logo

def generate_crest_png() -> bytes:
    S = 2048
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = 40
    # marigold ring (drawn first, slightly larger)
    draw.ellipse([pad, pad, S - pad, S - pad], fill=MARIGOLD)
    # navy disc on top, leaving a thin ring visible
    ring = 36
    draw.ellipse([pad + ring, pad + ring, S - pad - ring, S - pad - ring], fill=NAVY)

    # "LS" monogram
    font = ImageFont.truetype(FONT_BOLD, 760)
    draw.text((S / 2, S / 2 - 140), "LS", font=font, fill="white", anchor="mm")

    # small book-glyph motif beneath the monogram
    cx, cy = S / 2, S / 2 + 470
    w, h = 340, 110
    draw.polygon(
        [(cx - w, cy - h * 0.3), (cx, cy + h * 0.5), (cx, cy - h * 0.6), (cx - w * 0.15, cy - h)],
        fill=MARIGOLD,
    )
    draw.polygon(
        [(cx + w, cy - h * 0.3), (cx, cy + h * 0.5), (cx, cy - h * 0.6), (cx + w * 0.15, cy - h)],
        fill=MARIGOLD,
    )

    img = img.resize((512, 512), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def ensure_logo_file() -> str:
    from frappe.utils.file_manager import save_file
    png_bytes = generate_crest_png()
    file_doc = save_file("lsps_logo.png", png_bytes, dt=None, dn=None, is_private=0, decode=False)
    log(f"Logo file -> {file_doc.file_url}")
    return file_doc.file_url


# ---------------------------------------------------------------- 2. desk branding

def ensure_color(name, hex_value):
    if not frappe.db.exists("Color", name):
        frappe.get_doc({"doctype": "Color", "name": name, "color": hex_value}).insert(ignore_permissions=True)
    return name


def ensure_website_theme(logo_url):
    name = "Little Scholars"
    navy = ensure_color("LSPS Navy", NAVY)
    navy_dark = ensure_color("LSPS Navy Dark", NAVY_DARK)
    charcoal = ensure_color("LSPS Charcoal", CHARCOAL)
    parchment = ensure_color("LSPS Parchment", PARCHMENT)

    if frappe.db.exists("Website Theme", name):
        theme = frappe.get_doc("Website Theme", name)
    else:
        theme = frappe.new_doc("Website Theme")
        theme.theme = name
    theme.primary_color = navy
    theme.text_color = charcoal
    theme.dark_color = navy_dark
    theme.light_color = parchment
    theme.background_color = parchment
    theme.save(ignore_permissions=True)
    log(f"Website Theme '{name}'")
    return name


def setup_navbar_branding(logo_url):
    ns = frappe.get_single("Navbar Settings")
    ns.app_logo = logo_url
    ns.announcement_widget = (
        f"<p>Welcome to <b>{SCHOOL_NAME}</b> — Academic Year 2026-2027, Term 2 is now in session.</p>"
    )
    ns.announcement_widget_color = NAVY
    ns.dismissible_announcement_widget = 1
    ns.save(ignore_permissions=True)
    log("Navbar Settings branded")


def setup_system_and_website_settings(logo_url, theme_name):
    ss = frappe.get_single("System Settings")
    ss.app_name = SCHOOL_NAME
    # A site created headlessly via `bench new-site` skips the interactive
    # wizard step that normally sets these two mandatory fields — confirmed
    # the hard way ("MandatoryError: language, time_zone") on the first
    # all-in-one Docker run. India-appropriate defaults, matching the
    # Company's country.
    if not ss.language:
        ss.language = "en"
    if not ss.time_zone:
        ss.time_zone = "Asia/Kolkata"
    ss.save(ignore_permissions=True)

    ws = frappe.get_single("Website Settings")
    ws.app_name = SCHOOL_NAME
    ws.app_logo = logo_url
    ws.favicon = logo_url
    ws.website_theme = theme_name
    ws.save(ignore_permissions=True)
    log("System/Website Settings branded")


def setup_education_settings_branding(logo_url):
    es = frappe.get_single("Education Settings")
    es.school_college_logo = logo_url
    es.save(ignore_permissions=True)
    log("Education Settings logo set")


# ---------------------------------------------------------------- 3. workspace polish

def ensure_custom_html_block(name, html, style="", script=""):
    if frappe.db.exists("Custom HTML Block", name):
        # Self-healing: a block created by an earlier version of this script
        # (before `script` existed) won't have it set — fix that in place
        # rather than skipping, same pattern as fix_setup_wizard_flags.py.
        if script and frappe.db.get_value("Custom HTML Block", name, "script") != script:
            frappe.db.set_value("Custom HTML Block", name, "script", script)
            log(f"Custom HTML Block '{name}' script updated")
        return name
    frappe.get_doc({
        "doctype": "Custom HTML Block", "name": name,
        "html": html, "style": style, "script": script, "private": 0,
    }).insert(ignore_permissions=True)
    log(f"Custom HTML Block '{name}'")
    return name


# Frappe caps desk content at a fixed 900px column (centered) above the `lg`
# breakpoint — same var(--page-max-width) rule reused across Workspace/Form/
# List/Tree views, so it reads as "empty gap on the right" everywhere on a
# normal demo laptop screen. Frappe ships a real, supported escape hatch for
# exactly this (the navbar's "Toggle Full Width" feature — a body.full-width
# class + a localStorage flag, re-applied on every full page load by
# desk.js) but it's an opt-in per-browser toggle with no server-side default.
# Auto-flip it for every visitor via a Custom HTML Block's `script` field —
# that field is fieldtype "Code" (frappe/desk/doctype/custom_html_block),
# explicitly exempt from the HTML sanitizer that strips <script> tags from
# ordinary rich-text fields like Navbar Settings.announcement_widget
# (confirmed the hard way: sanitize_html() silently stripped a script tag
# added there). This rides Frappe's own tested CSS path instead of a custom
# override, and needs no core-file edits.
FULL_WIDTH_SCRIPT = (
    'document.body.classList.add("full-width");'
    'localStorage.setItem("container_fullwidth","true");'
)


def _content_has_block(content, block_type, key, value):
    return any(b.get("type") == block_type and b.get("data", {}).get(key) == value for b in content)


def polish_education_workspace(logo_url):
    ws = frappe.get_doc("Workspace", "Education")
    content = frappe.parse_json(ws.content) if ws.content else []

    banner_name = ensure_custom_html_block(
        "LSPS Welcome Banner",
        html=(
            f'<div style="display:flex;align-items:center;gap:16px;background:{NAVY};'
            f'border-radius:10px;padding:18px 24px;margin-bottom:8px;">'
            f'<img src="{logo_url}" style="width:52px;height:52px;border-radius:50%;" />'
            f'<div>'
            f'<div style="color:white;font-size:20px;font-weight:700;">{SCHOOL_NAME}</div>'
            f'<div style="color:{MARIGOLD};font-size:13px;">Academic Year 2026-2027 &middot; Term 2</div>'
            f'</div></div>'
        ),
        script=FULL_WIDTH_SCRIPT,
    )
    if banner_name not in {c.custom_block_name for c in ws.get("custom_blocks")}:
        ws.append("custom_blocks", {"custom_block_name": banner_name, "label": banner_name})
    if not _content_has_block(content, "custom_block", "custom_block_name", banner_name):
        content.insert(0, {"id": frappe.generate_hash(length=10), "type": "custom_block",
                            "data": {"custom_block_name": banner_name, "col": 12}})

    existing_qlists = {q.label for q in ws.get("quick_lists")}
    if "Fee Overdue Invoices" not in existing_qlists:
        ws.append("quick_lists", {
            "document_type": "Sales Invoice", "label": "Fee Overdue Invoices",
            "quick_list_filter": '[["Sales Invoice","status","=","Overdue"]]',
        })
    if not _content_has_block(content, "quick_list", "quick_list_name", "Fee Overdue Invoices"):
        content.append({"id": frappe.generate_hash(length=10), "type": "quick_list",
                         "data": {"quick_list_name": "Fee Overdue Invoices", "col": 12}})

    color_map = {"Student": "Blue", "Instructor": "Cyan", "Sales Invoice": "Orange"}
    for row in ws.get("shortcuts"):
        if row.label in color_map and row.color != color_map[row.label]:
            row.color = color_map[row.label]

    ws.content = frappe.as_json(content)
    ws.save(ignore_permissions=True)
    log("Education workspace polished")


def polish_teacher_portal_workspace(logo_url):
    ws = frappe.get_doc("Workspace", "Teacher Portal")
    content = frappe.parse_json(ws.content) if ws.content else []

    banner_name = ensure_custom_html_block(
        "LSPS Teacher Welcome Banner",
        html=(
            f'<div style="display:flex;align-items:center;gap:16px;background:{NAVY};'
            f'border-radius:10px;padding:18px 24px;margin-bottom:8px;">'
            f'<img src="{logo_url}" style="width:44px;height:44px;border-radius:50%;" />'
            f'<div>'
            f'<div style="color:white;font-size:18px;font-weight:700;">Welcome, Educator</div>'
            f'<div style="color:{MARIGOLD};font-size:13px;">{SCHOOL_NAME}</div>'
            f'</div></div>'
        ),
        script=FULL_WIDTH_SCRIPT,
    )
    if banner_name not in {c.custom_block_name for c in ws.get("custom_blocks")}:
        ws.append("custom_blocks", {"custom_block_name": banner_name, "label": banner_name})
    if not _content_has_block(content, "custom_block", "custom_block_name", banner_name):
        content.insert(0, {"id": frappe.generate_hash(length=10), "type": "custom_block",
                            "data": {"custom_block_name": banner_name, "col": 12}})

    existing_qlists = {q.label for q in ws.get("quick_lists")}
    if "This Week's Timetable" not in existing_qlists:
        ws.append("quick_lists", {
            "document_type": "Course Schedule", "label": "This Week's Timetable",
            "quick_list_filter": "",
        })
    if not _content_has_block(content, "quick_list", "quick_list_name", "This Week's Timetable"):
        content.append({"id": frappe.generate_hash(length=10), "type": "quick_list",
                         "data": {"quick_list_name": "This Week's Timetable", "col": 12}})

    ws.content = frappe.as_json(content)
    ws.save(ignore_permissions=True)
    log("Teacher Portal workspace polished")


# ---------------------------------------------------------------- run all

def run_all():
    logo_url = ensure_logo_file()
    setup_navbar_branding(logo_url)
    theme_name = ensure_website_theme(logo_url)
    setup_system_and_website_settings(logo_url, theme_name)
    setup_education_settings_branding(logo_url)
    frappe.db.commit()

    polish_education_workspace(logo_url)
    polish_teacher_portal_workspace(logo_url)
    frappe.db.commit()

    frappe.clear_cache()
    log("Done.")


if __name__ == "__main__":
    run_all()
    frappe.db.commit()
