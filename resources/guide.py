"""
Publishes a small landing page at /guide — no login required — that just
points to the two real guides: /school-guide and /health-guide. Replaces
what used to be one combined guide covering both modules' roles on a
single page; kept as a separate script (not deleted) so old links to
/guide keep working as a hub instead of breaking.

Run with:
    cd ~/frappe-bench/sites
    ../env/bin/python ../guide.py
"""
import os

import frappe

SITE_NAME = os.environ.get("SITE_NAME", "erp.localhost")
SITES_PATH = os.environ.get("SITES_PATH", "/Users/danishkhan/frappe-bench/sites")

frappe.init(site=SITE_NAME, sites_path=SITES_PATH)
frappe.connect()
frappe.set_user("Administrator")

ORG_NAME = "Little Scholars Public School"
ROUTE = "guide"
PAGE_VERSION = "1"


def log(msg):
    print(f"[guide] {msg}")


HTML_CONTENT = f"""
<div class="guide">
  <header class="g-hero">
    <div class="g-crest">LS</div>
    <p class="g-eyebrow">{ORG_NAME}</p>
    <h1>How to use this system</h1>
    <p class="g-dek">One system, two modules. Pick the one you work in for a full, step-by-step guide to your role.</p>
  </header>

  <div class="g-cards">
    <a class="g-card" href="/school-guide">
      <div class="g-card-icon">LS</div>
      <h2>School Guide</h2>
      <p>Principal/Admin, Registrar, Teacher, Accountant, and Student — everything about running the school.</p>
      <span class="g-card-cta">Open the School Guide &rarr;</span>
    </a>
    <a class="g-card g-card-health" href="/health-guide">
      <div class="g-card-icon g-card-icon-health">+</div>
      <h2>Health Guide</h2>
      <p>Hospital Admin, Doctor, Nurse, Front Desk, and Lab Technician — everything about running the hospital module.</p>
      <span class="g-card-cta">Open the Health Guide &rarr;</span>
    </a>
  </div>

  <p class="g-hint">Not sure which one? Ask whoever gave you your login — it depends on which part of the school you work in.</p>

  <footer class="g-footer">
    <p>{ORG_NAME} &middot; these pages need no login and can be shared as a link.</p>
  </footer>
</div>
"""

CSS_CONTENT = """
.guide{
  --navy: #1B3B6F;
  --navy-dark: #12294D;
  --marigold: #F2A93B;
  --charcoal: #4A5568;
  --parchment: #FDF8F0;
  --border: #E7DFC9;
  max-width: 720px;
  margin: 0 auto;
  padding: 8px 4px 40px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: var(--charcoal);
  line-height: 1.65;
}
.guide h1, .guide h2{ font-family: Georgia, "Times New Roman", serif; color: var(--navy-dark); }
.g-hero{ text-align: center; padding: 20px 0 30px; }
.g-crest{
  width: 56px; height: 56px; border-radius: 50%;
  background: var(--navy); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-family: Georgia, serif; font-weight: 700; font-size: 20px;
  margin: 0 auto 14px; border: 3px solid var(--marigold);
}
.g-eyebrow{ text-transform: uppercase; letter-spacing: .08em; font-size: 12px; color: var(--marigold); font-weight: 700; margin: 0 0 6px; }
.g-hero h1{ font-size: 30px; margin: 0 0 10px; }
.g-dek{ color: var(--charcoal); max-width: 46ch; margin: 0 auto; font-size: 15.5px; }

.g-cards{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin: 10px 0 22px; }
@media (max-width: 600px){ .g-cards{ grid-template-columns: 1fr; } }

.g-card{
  display: block; text-decoration: none; color: inherit;
  background: var(--parchment); border: 1px solid var(--border); border-radius: 14px;
  padding: 26px 22px; transition: transform .1s ease, box-shadow .1s ease;
}
.g-card:hover{ transform: translateY(-2px); box-shadow: 0 6px 18px rgba(27,59,111,.12); }
.g-card h2{ font-size: 20px; margin: 4px 0 8px; }
.g-card p{ font-size: 14px; color: var(--charcoal); margin: 0 0 14px; }
.g-card-icon{
  width: 44px; height: 44px; border-radius: 50%;
  background: var(--navy); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-family: Georgia, serif; font-weight: 700; font-size: 16px;
  margin-bottom: 10px; border: 2px solid var(--marigold);
}
.g-card-icon-health{ background: #B23B4E; font-size: 22px; }
.g-card-cta{ font-size: 13.5px; font-weight: 700; color: var(--navy); }
.g-card-health .g-card-cta{ color: #B23B4E; }

.g-hint{ text-align: center; font-size: 13.5px; color: var(--charcoal); margin: 8px 0 30px; }

.g-footer{
  border-top: 1px solid var(--border); margin-top: 20px; padding-top: 16px;
  text-align: center; font-size: 12.5px; color: var(--charcoal);
}

@media (max-width: 480px){
  .guide{ padding: 4px 2px 30px; }
  .g-hero h1{ font-size: 24px; }
}
"""


def ensure_guide_page():
    version_marker = f"<!-- guide-landing-version:{PAGE_VERSION} -->"
    full_html = HTML_CONTENT + version_marker

    if frappe.db.exists("Web Page", {"route": ROUTE}):
        page = frappe.get_doc("Web Page", {"route": ROUTE})
        if version_marker in (page.main_section_html or "") and page.title == "Guide":
            log(f"'/{ROUTE}' already up to date (v{PAGE_VERSION})")
            return
        page.title = "Guide"  # self-heal: this page used to be the old combined "User Guide"
        page.main_section_html = full_html
        page.css = CSS_CONTENT
        page.save(ignore_permissions=True)
        log(f"'/{ROUTE}' updated to v{PAGE_VERSION}")
        return

    frappe.get_doc({
        "doctype": "Web Page",
        "title": "Guide",
        "route": ROUTE,
        "published": 1,
        "content_type": "HTML",
        "main_section_html": full_html,
        "css": CSS_CONTENT,
        "full_width": 1,
        "show_title": 0,
        "show_sidebar": 0,
        "meta_title": f"System Guide — {ORG_NAME}",
        "meta_description": "Pick your module — School Guide or Health Guide — no login required to view.",
    }).insert(ignore_permissions=True)
    log(f"'/{ROUTE}' created (v{PAGE_VERSION}) — no login required")


def run_all():
    ensure_guide_page()
    frappe.db.commit()
    frappe.clear_cache()
    log("Done.")


if __name__ == "__main__":
    run_all()
    frappe.db.commit()
