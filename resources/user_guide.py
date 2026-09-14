"""
Publishes a single public (no-login) Web Page at /guide — a plain-language,
role-by-role walkthrough of the school ERP for staff and students. This is
the ONE place non-technical users are pointed to; it deliberately never
includes real passwords (this page needs no login to view, so a secret
printed on it would be visible to anyone with the link) — only the login
flow, the URL to use, and what each role does once inside.

Run after seed_school.py (needs Company/roles to exist for the content to
be accurate) as part of the same boot-time branding pass. Idempotent: safe
to rerun, self-heals content on a version bump (see PAGE_VERSION below).

Run with:
    cd ~/frappe-bench/sites
    ../env/bin/python ../user_guide.py
"""
import os

import frappe

SITE_NAME = os.environ.get("SITE_NAME", "erp.localhost")
SITES_PATH = os.environ.get("SITES_PATH", "/Users/danishkhan/frappe-bench/sites")

frappe.init(site=SITE_NAME, sites_path=SITES_PATH)
frappe.connect()
frappe.set_user("Administrator")

SCHOOL_NAME = "Little Scholars Public School"
ROUTE = "guide"

# Bump this whenever HTML_CONTENT/CSS_CONTENT changes, so a site that already
# has an older version of the page picks up the new one on next boot instead
# of silently keeping stale content forever (same self-healing pattern as
# ensure_custom_html_block in ui_polish.py).
PAGE_VERSION = "1"


def log(msg):
    print(f"[guide] {msg}")


HTML_CONTENT = f"""
<div class="guide">

  <header class="g-hero">
    <div class="g-crest">LS</div>
    <p class="g-eyebrow">{SCHOOL_NAME}</p>
    <h1>How to use the school system</h1>
    <p class="g-dek">Everything you need is on this one page — find your role below and follow the steps. No technical knowledge needed.</p>
  </header>

  <nav class="g-jump" aria-label="Jump to your role">
    <span class="g-jump-label">I am a&hellip;</span>
    <a href="#principal">Principal / Admin</a>
    <a href="#registrar">Registrar</a>
    <a href="#teacher">Teacher</a>
    <a href="#accountant">Accountant</a>
    <a href="#student">Student</a>
  </nav>

  <section id="login" class="g-section">
    <h2><span class="g-tag">Start here</span>Logging in</h2>
    <ol class="g-steps">
      <li>Open this website's address in any browser — on a phone, tablet, or computer.</li>
      <li>Click <strong>Sign In</strong> if it doesn't appear automatically.</li>
      <li>Enter the <strong>email address</strong> and <strong>password</strong> given to you by the school office. If you don't have one yet, ask the school office.</li>
      <li>Click <strong>Continue</strong>.</li>
    </ol>
    <div class="g-note">
      <p><strong>Students:</strong> you'll be taken to a different, simpler screen than staff — see the <a href="#student">Student</a> section below.</p>
    </div>
    <div class="g-note">
      <p><strong>Staff:</strong> after logging in you may briefly see a screen with just three icons (<em>ERPNext</em>, <em>Education</em>, <em>Framework</em>). Click <strong>Education</strong> — that's the one you want.</p>
    </div>
  </section>

  <section id="principal" class="g-section g-role">
    <h2><span class="g-tag">Role</span>Principal / Admin</h2>
    <p class="g-role-summary">You see everything: every student, every teacher, every fee invoice, and every report — across the whole school.</p>

    <h3>What you'll see</h3>
    <p>After clicking <strong>Education</strong>, you land on the main school dashboard. Along the top are quick numbers — total active students, active instructors, programs and courses — and how many fee invoices are still unpaid. Below that are grouped links to every part of the system: Student Management, Academics, Admissions, Assessment, Fee Management, and Attendance.</p>

    <h3>Common tasks</h3>
    <ol class="g-steps">
      <li><strong>Check overall enrollment.</strong> The "Student" number at the top of the dashboard is always live — click it to see the full list.</li>
      <li><strong>Check fee collection.</strong> Click the "Sales Invoice" number (shown in orange if there are unpaid ones) to see every invoice and its status: Paid, Unpaid, or Overdue.</li>
      <li><strong>Look at a report.</strong> Scroll to "Reports &amp; Masters" and pick a category — for example "Attendance" to see attendance reports, or "Fee Management" for fee-related lists.</li>
      <li><strong>Open any record.</strong> Everything in this system works the same way: click a list (like "Student"), then click any row to open the full record, then use the <strong>Edit</strong>/<strong>Save</strong> buttons to make changes.</li>
    </ol>
  </section>

  <section id="registrar" class="g-section g-role">
    <h2><span class="g-tag">Role</span>Registrar</h2>
    <p class="g-role-summary">You manage student records, admissions, and enrollment — day-to-day school administration.</p>

    <h3>What you'll see</h3>
    <p>The same school dashboard as the Principal, but you won't see fee/invoice numbers — that part belongs to the Accountant.</p>

    <h3>Common tasks</h3>
    <ol class="g-steps">
      <li><strong>Add a new student.</strong> In the left sidebar, click <strong>Student</strong>, then the <strong>+ Add Student</strong> (or "New") button at the top right. Fill in the student's details and click <strong>Save</strong>.</li>
      <li><strong>Process a new admission.</strong> Click <strong>Student Applicant</strong> under the Admissions section to see everyone who has applied. Open an application to review it and change its status as it progresses.</li>
      <li><strong>Enroll a student in a program.</strong> Click <strong>Program Enrollment</strong>, then <strong>New</strong>, choose the student and the program/academic year, and <strong>Save</strong>.</li>
      <li><strong>Update a guardian's contact details.</strong> Click <strong>Guardian</strong> in the sidebar, find the guardian's name, open the record, edit, and <strong>Save</strong>.</li>
      <li><strong>See which class a student is in.</strong> Click <strong>Student Group</strong> to see every class/section and its student list.</li>
    </ol>
  </section>

  <section id="teacher" class="g-section g-role">
    <h2><span class="g-tag">Role</span>Teacher</h2>
    <p class="g-role-summary">You only see your own classes — your timetable, your students' attendance, and your students' grades.</p>

    <h3>What you'll see</h3>
    <p>After logging in, click <strong>Teacher Portal</strong> in the left sidebar (if it isn't already open). You'll see a welcome banner, then three shortcuts — <strong>My Timetable</strong>, <strong>Mark Attendance</strong>, and <strong>Enter Grades</strong> — each showing how many records you have. Below that is an attendance chart and this week's class schedule.</p>

    <h3>Common tasks</h3>
    <ol class="g-steps">
      <li><strong>Check your timetable.</strong> Click <strong>My Timetable</strong>, or just look at "This Week's Timetable" on the portal home — it lists each class you're teaching, in order.</li>
      <li>
        <strong>Mark attendance.</strong>
        <ol class="g-substeps">
          <li>Click <strong>Mark Attendance</strong>.</li>
          <li>Click <strong>New</strong>, choose the class (Student Group) and the date.</li>
          <li>Click <strong>Get Students</strong> to load the class list.</li>
          <li>Mark each student Present, Absent, or on Leave.</li>
          <li>Click <strong>Save</strong>, then <strong>Submit</strong> to finalize it.</li>
        </ol>
      </li>
      <li>
        <strong>Enter grades.</strong>
        <ol class="g-substeps">
          <li>Click <strong>Enter Grades</strong>.</li>
          <li>Open the assessment for your class and subject (your school admin sets these up in advance).</li>
          <li>Enter each student's score.</li>
          <li>Click <strong>Save</strong>, then <strong>Submit</strong> once you're done — a submitted grade is final and visible to the student.</li>
        </ol>
      </li>
    </ol>
    <div class="g-note">
      <p>You'll only ever see the classes assigned to you — this is intentional, not a limitation to work around.</p>
    </div>
  </section>

  <section id="accountant" class="g-section g-role">
    <h2><span class="g-tag">Role</span>Accountant / Fee Clerk</h2>
    <p class="g-role-summary">You manage fee invoices and payments — you won't see student academic records.</p>

    <h3>What you'll see</h3>
    <p>After logging in you'll land on the app-picker screen — click <strong>ERPNext</strong>. Use the search bar at the top (or the sidebar) and type <strong>Sales Invoice</strong> to see every fee invoice raised by the school, with its status.</p>

    <h3>Common tasks</h3>
    <ol class="g-steps">
      <li><strong>Find unpaid or overdue fees.</strong> Open <strong>Sales Invoice</strong>, then use the <strong>Status</strong> filter at the top of the list and choose "Unpaid" or "Overdue".</li>
      <li>
        <strong>Record a payment.</strong>
        <ol class="g-substeps">
          <li>Open the specific invoice from the list.</li>
          <li>Click <strong>Create</strong>, then <strong>Payment</strong> (this pre-fills the amount from the invoice).</li>
          <li>Check the amount and payment method, then click <strong>Save</strong>, then <strong>Submit</strong>.</li>
          <li>The invoice's status updates automatically to "Paid" (or stays "Unpaid" if it was only a partial payment).</li>
        </ol>
      </li>
      <li><strong>Create a new invoice.</strong> From the Sales Invoice list, click <strong>+ Add Sales Invoice</strong>, choose the student/customer, add the fee items, and <strong>Save</strong>, then <strong>Submit</strong>.</li>
    </ol>
  </section>

  <section id="student" class="g-section g-role">
    <h2><span class="g-tag">Role</span>Student</h2>
    <p class="g-role-summary">You have your own simple portal — your timetable, your grades, your fees, and your attendance record.</p>

    <h3>What you'll see</h3>
    <p>Log in the same way as everyone else. Students are taken to a different, much simpler screen automatically — with four tabs on the left: <strong>Schedule</strong>, <strong>Grades</strong>, <strong>Fees</strong>, and <strong>Attendance</strong>.</p>
    <div class="g-note">
      <p>If you're not taken there automatically, go to this website's address and add <code>/student-portal</code> to the end of it.</p>
    </div>

    <h3>What each tab shows</h3>
    <ol class="g-steps">
      <li><strong>Schedule.</strong> A calendar of your classes for the month — click any day with classes to see the subject and time.</li>
      <li><strong>Grades.</strong> Your scores for each subject, by exam. Choose your class at the top if more than one is listed.</li>
      <li><strong>Fees.</strong> Every fee due for you, its due date, and its status. If a fee shows <strong>Pay Now</strong>, click it to pay online.</li>
      <li><strong>Attendance.</strong> Your attendance record for the term.</li>
    </ol>
  </section>

  <section id="help" class="g-section">
    <h2><span class="g-tag">Good to know</span>General tips</h2>
    <ol class="g-steps">
      <li><strong>To log out:</strong> click your name in the bottom-left corner of the sidebar, then <strong>Logout</strong>.</li>
      <li><strong>Forgot your password?</strong> Contact the school office — they can reset it for you.</li>
      <li><strong>The blue banner at the top</strong> can be closed with the &times; on its right — it's just a welcome message and closing it doesn't affect anything else.</li>
      <li><strong>Every list in this system works the same way:</strong> click a row to open it, use the buttons at the top-right to add new records, edit, save, or submit.</li>
      <li><strong>Still stuck?</strong> Contact the school office for help.</li>
    </ol>
  </section>

  <footer class="g-footer">
    <p>{SCHOOL_NAME} &middot; this page needs no login and can be reached any time at <code>/guide</code>.</p>
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
  max-width: 760px;
  margin: 0 auto;
  padding: 8px 4px 40px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: var(--charcoal);
  line-height: 1.65;
}
.guide h1, .guide h2, .guide h3{
  font-family: Georgia, "Times New Roman", serif;
  color: var(--navy-dark);
}
.g-hero{ text-align: center; padding: 20px 0 26px; border-bottom: 1px solid var(--border); margin-bottom: 22px; }
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

.g-jump{
  display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
  justify-content: center; margin-bottom: 34px;
}
.g-jump-label{ font-size: 13px; color: var(--charcoal); margin-right: 4px; }
.g-jump a{
  font-size: 13.5px; text-decoration: none; color: var(--navy);
  border: 1px solid var(--border); background: var(--parchment);
  padding: 6px 13px; border-radius: 999px;
}
.g-jump a:hover{ background: var(--navy); color: #fff; border-color: var(--navy); }

.g-section{ margin-bottom: 40px; }
.g-section h2{
  font-size: 21px; margin: 0 0 4px; display: flex; align-items: center; gap: 10px;
}
.g-tag{
  font-family: -apple-system, sans-serif; text-transform: uppercase; letter-spacing: .06em;
  font-size: 10.5px; font-weight: 700; color: #fff; background: var(--marigold);
  padding: 3px 9px; border-radius: 5px; white-space: nowrap;
}
.g-role{ border-top: 3px solid var(--navy); padding-top: 18px; }
.g-role-summary{ font-size: 15.5px; color: var(--navy-dark); margin: 0 0 18px; }
.g-section h3{ font-size: 15px; margin: 20px 0 8px; }

.g-steps{ padding-left: 1.4em; margin: 0 0 14px; }
.g-steps > li{ margin-bottom: 11px; }
.g-substeps{ padding-left: 1.3em; margin: 8px 0 0; }
.g-substeps li{ margin-bottom: 6px; font-size: 14.5px; }

.g-note{
  background: var(--parchment); border-left: 3px solid var(--marigold);
  border-radius: 0 8px 8px 0; padding: 10px 16px; margin: 12px 0 16px;
  font-size: 14.5px;
}
.g-note p{ margin: 0; }
.guide code{
  background: var(--parchment); border: 1px solid var(--border);
  padding: 1px 6px; border-radius: 4px; font-size: .92em;
}

.g-footer{
  border-top: 1px solid var(--border); margin-top: 30px; padding-top: 16px;
  text-align: center; font-size: 12.5px; color: var(--charcoal);
}

@media (max-width: 480px){
  .guide{ padding: 4px 2px 30px; }
  .g-hero h1{ font-size: 24px; }
}
"""


def ensure_guide_page():
    version_marker = f"<!-- guide-version:{PAGE_VERSION} -->"
    full_html = HTML_CONTENT + version_marker

    if frappe.db.exists("Web Page", {"route": ROUTE}):
        page = frappe.get_doc("Web Page", {"route": ROUTE})
        if version_marker in (page.main_section_html or ""):
            log(f"'/{ROUTE}' already up to date (v{PAGE_VERSION})")
            return
        page.main_section_html = full_html
        page.css = CSS_CONTENT
        page.save(ignore_permissions=True)
        log(f"'/{ROUTE}' updated to v{PAGE_VERSION}")
        return

    frappe.get_doc({
        "doctype": "Web Page",
        "title": "User Guide",
        "route": ROUTE,
        "published": 1,
        "content_type": "HTML",
        "main_section_html": full_html,
        "css": CSS_CONTENT,
        "full_width": 1,
        "show_title": 0,
        "show_sidebar": 0,
        "meta_title": f"How to use the school system — {SCHOOL_NAME}",
        "meta_description": "Role-by-role guide for staff and students — no login required to view.",
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
