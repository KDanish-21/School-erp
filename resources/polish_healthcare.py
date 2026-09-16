"""
Friendlier terminology for the Healthcare (Marley) module — same idempotent
ORM-script pattern as ui_polish.py, run after seed_hospital.py.

Two safe, non-destructive mechanisms (confirmed against Frappe's own
source — deliberately NEVER renames a DocType itself, which would break
every hardcoded reference to it inside the app's own .py/.js/hooks.py):

  1. `Translation` rows (language "en") for whole-term renames that need to
     show up everywhere — breadcrumbs, sidebar, menus. Confirmed English
     translations do load (no `lang == "en"` skip anywhere in
     frappe/translate.py or boot.py).
  2. `Property Setter` rows (doctype_or_field="DocField", property="label")
     for individual confusing field labels. Confirmed
     `PropertySetter.validate()` auto-clears the relevant doctype's cache —
     no manual `frappe.clear_cache(doctype=...)` needed afterward.

Never touches a Select field's stored option *values* (only a field's own
label) — the app's own Python very likely branches on the literal status
strings ("Scheduled", "Open", etc.), so changing those would silently
break real functionality; only what a field/doctype is CALLED changes.

Run with:
    cd ~/frappe-bench/sites
    ../env/bin/python ../polish_healthcare.py
"""
import os

import frappe

SITE_NAME = os.environ.get("SITE_NAME", "erp.localhost")
SITES_PATH = os.environ.get("SITES_PATH", "/Users/danishkhan/frappe-bench/sites")

frappe.init(site=SITE_NAME, sites_path=SITES_PATH)
frappe.connect()
frappe.set_user("Administrator")


def log(msg):
    print(f"[healthcare-polish] {msg}")


# Whole-term renames. Checked each against collision risk before adding:
# none of these exact phrases are used as a doctype/label elsewhere in
# ERPNext or Education on this site.
TERM_TRANSLATIONS = {
    "Patient Encounter": "Consultation",
    "Healthcare Practitioner": "Doctor",
    "Clinical Procedure": "Procedure",
    "Healthcare Service Unit": "Room / Ward",
    "Fee Validity": "Free Follow-up Pass",
    "Inpatient Record": "Admission",
}

# Individual field-label fixes — the "Prescription" field on both of these
# reads as a drug order to anyone not already familiar with the app; it's
# actually "which visit/order this came from."
FIELD_LABELS = [
    ("Lab Test", "prescription", "Ordered From"),
    ("Clinical Procedure", "procedure_prescription", "Ordered From"),
]

# Healthcare workspace shortcut relabels — `label` and `link_to` are
# independent fields on Workspace Shortcut, so this only changes the tile
# text; the underlying doctype it opens is untouched.
SHORTCUT_LABELS = {
    "Healthcare Practitioner": "Doctors",
    "Healthcare Service Unit": "Rooms & Wards",
}


def ensure_translation(source_text, translated_text):
    existing = frappe.db.exists("Translation", {"source_text": source_text, "language": "en"})
    if existing:
        if frappe.db.get_value("Translation", existing, "translated_text") != translated_text:
            frappe.db.set_value("Translation", existing, "translated_text", translated_text)
        return
    frappe.get_doc({
        "doctype": "Translation",
        "language": "en",
        "source_text": source_text,
        "translated_text": translated_text,
    }).insert(ignore_permissions=True)


def setup_term_translations():
    for source, friendly in TERM_TRANSLATIONS.items():
        ensure_translation(source, friendly)
    frappe.db.commit()
    log(f"{len(TERM_TRANSLATIONS)} term translations")


def ensure_field_label(doctype, fieldname, label):
    ps_name = frappe.db.exists("Property Setter", {
        "doc_type": doctype, "field_name": fieldname, "property": "label",
    })
    if ps_name:
        if frappe.db.get_value("Property Setter", ps_name, "value") != label:
            frappe.db.set_value("Property Setter", ps_name, "value", label)
        return
    frappe.get_doc({
        "doctype": "Property Setter",
        "doctype_or_field": "DocField",
        "doc_type": doctype,
        "field_name": fieldname,
        "property": "label",
        "value": label,
        "property_type": "Data",
    }).insert(ignore_permissions=True)


def setup_field_labels():
    for doctype, fieldname, label in FIELD_LABELS:
        ensure_field_label(doctype, fieldname, label)
    frappe.db.commit()
    log(f"{len(FIELD_LABELS)} field label overrides")


def setup_workspace_shortcuts():
    if not frappe.db.exists("Workspace", "Healthcare"):
        log("Healthcare workspace not found — skipping shortcut relabel")
        return
    ws = frappe.get_doc("Workspace", "Healthcare")
    changed = False
    old_to_new = {}
    for row in ws.get("shortcuts"):
        if row.link_to in SHORTCUT_LABELS and row.label != SHORTCUT_LABELS[row.link_to]:
            old_to_new[row.label] = SHORTCUT_LABELS[row.link_to]
            row.label = SHORTCUT_LABELS[row.link_to]
            changed = True

    if old_to_new:
        # The page's `content` JSON layout resolves each shortcut tile by
        # `shortcut_name` matched against the child-table row's CURRENT
        # `label` — not a stable id — confirmed the hard way: relabeling
        # only the child-table row silently broke rendering for both tiles
        # (they simply vanished from the page, no error). Content and
        # label have to be kept in sync on every rename.
        content = frappe.parse_json(ws.content) if ws.content else []
        for block in content:
            if block.get("type") == "shortcut":
                name = block.get("data", {}).get("shortcut_name")
                if name in old_to_new:
                    block["data"]["shortcut_name"] = old_to_new[name]
        ws.content = frappe.as_json(content)

    if changed:
        ws.save(ignore_permissions=True)
    log("Healthcare workspace shortcuts relabeled")


def run_all():
    setup_term_translations()
    setup_field_labels()
    setup_workspace_shortcuts()
    frappe.db.commit()
    frappe.clear_cache()
    log("Done.")


if __name__ == "__main__":
    run_all()
    frappe.db.commit()
