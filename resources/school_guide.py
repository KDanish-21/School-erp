"""
Publishes a deep, plain-language guide for the SCHOOL module only, at
/school-guide — no login required to view. Companion to health_guide.py
(hospital module) and guide.py (a small landing page linking to both).

Split out from what used to be a single combined /guide page: the user
explicitly wants one guide per module, not roles from both modules mixed
onto one page, so each guide can go deep on its own subject without
splitting the reader's attention.

Run with:
    cd ~/frappe-bench/sites
    ../env/bin/python ../school_guide.py
"""
import os

import frappe

SITE_NAME = os.environ.get("SITE_NAME", "erp.localhost")
SITES_PATH = os.environ.get("SITES_PATH", "/Users/danishkhan/frappe-bench/sites")

frappe.init(site=SITE_NAME, sites_path=SITES_PATH)
frappe.connect()
frappe.set_user("Administrator")

SCHOOL_NAME = "Little Scholars Public School"
ROUTE = "school-guide"
PAGE_VERSION = "1"


def log(msg):
    print(f"[school-guide] {msg}")


HTML_CONTENT = f"""
<div class="guide">

  <a class="g-back" href="/guide">&larr; All guides</a>

  <header class="g-hero">
    <div class="g-crest">LS</div>
    <p class="g-eyebrow">{SCHOOL_NAME}</p>
    <h1>The School Guide</h1>
    <p class="g-dek">Everything about running the school on this system — how it's organized, what each role does, and every common task explained step by step.</p>
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
      <li>Enter the <strong>email address</strong> and <strong>password</strong> given to you by the office. If you don't have one yet, ask the office.</li>
      <li>Click <strong>Continue</strong>.</li>
    </ol>
    <div class="g-note">
      <p><strong>Students:</strong> you'll be taken to a different, simpler screen than staff — see the <a href="#student">Student</a> section below.</p>
    </div>
    <div class="g-note">
      <p><strong>Staff:</strong> after logging in you may briefly see a screen with a few icons (<em>ERPNext</em>, <em>Education</em>, <em>Marley Health</em>, <em>Framework</em>). Click <strong>Education</strong> — that's the school side of the system.</p>
    </div>
  </section>

  <section id="concepts" class="g-section">
    <h2><span class="g-tag">Before you start</span>How the school side is organized</h2>
    <p class="g-role-summary">A handful of ideas come up everywhere in this system — understanding them once makes every screen below make sense.</p>
    <div class="g-glossary">
      <div class="g-gterm"><strong>Student</strong><span>One record per child — their name, contact details, and their whole history in the school lives here.</span></div>
      <div class="g-gterm"><strong>Program</strong><span>A grade or class level, e.g. "Class 3" — the overall year a student is enrolled in.</span></div>
      <div class="g-gterm"><strong>Student Group</strong><span>A specific section within a grade, e.g. "Class 3 - Section A" — this is the actual "class" a teacher teaches and takes attendance for.</span></div>
      <div class="g-gterm"><strong>Course</strong><span>A subject, e.g. Mathematics or Science — taught within a Student Group on a schedule.</span></div>
      <div class="g-gterm"><strong>Fee Structure / Fee Schedule</strong><span>The fee plan for a program, and the actual bills raised from it — this is what becomes a Sales Invoice.</span></div>
      <div class="g-gterm"><strong>Sales Invoice</strong><span>An actual fee bill for one student — this is what shows Paid / Unpaid / Overdue.</span></div>
      <div class="g-gterm"><strong>Assessment Plan / Assessment Result</strong><span>An exam definition, and each student's actual score for it.</span></div>
    </div>
    <div class="g-note">
      <p><strong>One habit that works everywhere in this system:</strong> click a list in the sidebar to see everything of that kind → click any row to open the full record → use <strong>Edit</strong>/<strong>Save</strong> (and <strong>Submit</strong> where it appears) to make it official. Nearly every task below is a variation of this.</p>
    </div>
  </section>

  <section id="principal" class="g-section g-role">
    <h2><span class="g-tag">Role</span>Principal / Admin</h2>
    <p class="g-role-summary">You see everything: every student, every teacher, every fee invoice, and every report — across the whole school. Nothing is hidden from this role.</p>

    <h3>What you'll see</h3>
    <p>After clicking <strong>Education</strong>, you land on the main school dashboard. Along the top: a live chart plus four numbers — total active students, active instructors, programs and courses — and how many fee invoices are still unpaid (shown in orange when there are any). Below that, "Reports &amp; Masters" groups every part of the system into cards: Student Management, Academics, Admissions, Assessment, Fee Management, and Attendance.</p>

    <h3>Common tasks</h3>
    <ol class="g-steps">
      <li><strong>Check overall enrollment.</strong> The "Student" number at the top of the dashboard is always live — click it to see the full list, or use the Student Management card for a more detailed breakdown by group.</li>
      <li><strong>Check fee collection at a glance.</strong> Click the "Sales Invoice" number (orange if anything is unpaid) to see every invoice and its status: Paid, Unpaid, or Overdue. Sort or filter by Status to focus on what's outstanding.</li>
      <li><strong>Review attendance across the school.</strong> Open the "Attendance" card and pick a report — you can see absence patterns by class or by student.</li>
      <li><strong>Check exam results.</strong> Open "Assessment" to see every Assessment Plan and drill into results by student or by subject.</li>
      <li><strong>Add or adjust a teacher's access.</strong> Open the <strong>User</strong> list (search for it in the top search bar), find the teacher, and check their Role Profile — this controls what they can see.</li>
      <li><strong>See the whole picture for one student.</strong> Open their Student record — it links out to their enrollments, attendance, fees, and results, so you don't have to hunt across separate lists.</li>
      <li><strong>Run a report for a governing body or parent meeting.</strong> Most list views have a <strong>Report View</strong> toggle (top right) that lets you add columns, group, and export to Excel.</li>
    </ol>
    <div class="g-note">
      <p><strong>This role can do everything below too</strong> — Registrar, Teacher, and Accountant tasks are all reachable from the same login, since nothing is restricted for Principal/Admin.</p>
    </div>
  </section>

  <section id="registrar" class="g-section g-role">
    <h2><span class="g-tag">Role</span>Registrar</h2>
    <p class="g-role-summary">You manage student records, admissions, and enrollment — day-to-day school administration. You won't see fee/invoice numbers on the dashboard; that's the Accountant's area.</p>

    <h3>What you'll see</h3>
    <p>The same Education workspace as the Principal, with the Student Management and Admissions cards being where you'll spend most of your time.</p>

    <h3>Common tasks</h3>
    <ol class="g-steps">
      <li><strong>Add a new student.</strong> In the left sidebar, click <strong>Student</strong>, then <strong>+ Add Student</strong> at the top right. Fill in their details and click <strong>Save</strong>.</li>
      <li><strong>Process a new admission.</strong> Click <strong>Student Applicant</strong> under Admissions to see everyone who has applied. Open an application to review it and move it forward as a decision is made.</li>
      <li><strong>Turn an accepted applicant into an enrolled student.</strong> From the Student Applicant record, there's an action to create the actual Student record once they're accepted — this avoids re-typing their details.</li>
      <li><strong>Enroll a student in a program.</strong> Click <strong>Program Enrollment</strong>, then <strong>New</strong>, choose the student and the program/academic year, and <strong>Save</strong>.</li>
      <li><strong>Put a student into a specific class/section.</strong> Click <strong>Student Group</strong>, open the right grade+section, and add the student to its list — this is what makes them show up for that teacher's attendance and grading.</li>
      <li><strong>Update a guardian's contact details.</strong> Click <strong>Guardian</strong> in the sidebar, find the guardian's name, open the record, edit, and <strong>Save</strong>.</li>
      <li><strong>Look up which class a student is in.</strong> Open their Student record, or check the Student Group list directly.</li>
      <li><strong>Handle a withdrawal or transfer.</strong> Open the Student record and update their status field — this keeps their history intact rather than deleting anything.</li>
    </ol>
  </section>

  <section id="teacher" class="g-section g-role">
    <h2><span class="g-tag">Role</span>Teacher</h2>
    <p class="g-role-summary">You only see your own classes — your timetable, your students' attendance, and your students' grades. This is intentional scoping, not a limitation to work around.</p>

    <h3>What you'll see</h3>
    <p>After logging in, click <strong>Teacher Portal</strong> in the left sidebar. You'll see a welcome banner, then three shortcuts — <strong>My Timetable</strong>, <strong>Mark Attendance</strong>, and <strong>Enter Grades</strong> — each showing a live count. Below that: an attendance trend chart and this week's class schedule.</p>

    <h3>Common tasks</h3>
    <ol class="g-steps">
      <li><strong>Check your timetable.</strong> Click <strong>My Timetable</strong>, or look at "This Week's Timetable" right on the portal home — it lists each class you're teaching, in order.</li>
      <li>
        <strong>Mark attendance.</strong>
        <ol class="g-substeps">
          <li>Click <strong>Mark Attendance</strong>.</li>
          <li>Click <strong>New</strong>, choose the class (Student Group) and the date.</li>
          <li>Click <strong>Get Students</strong> to load the class list.</li>
          <li>Mark each student Present, Absent, or on Leave.</li>
          <li>Click <strong>Save</strong>, then <strong>Submit</strong> to finalize it — a submitted attendance record is what counts toward reports.</li>
        </ol>
      </li>
      <li>
        <strong>Enter grades for an exam.</strong>
        <ol class="g-substeps">
          <li>Click <strong>Enter Grades</strong>.</li>
          <li>Open the assessment for your class and subject (the school admin sets these up in advance under Assessment Plan).</li>
          <li>Enter each student's score.</li>
          <li>Click <strong>Save</strong>, then <strong>Submit</strong> once you're done — a submitted grade is final and visible to the student on their own portal.</li>
        </ol>
      </li>
      <li><strong>Check a specific student's history.</strong> Open <strong>Student</strong> (still scoped to your own classes) and click into their record for past attendance and grades.</li>
      <li><strong>Fix a mistake after submitting.</strong> Open the submitted Attendance or Assessment Result record and use <strong>Cancel</strong>, then re-enter it correctly — submitted records can't be edited directly, this keeps a clean history.</li>
    </ol>
  </section>

  <section id="accountant" class="g-section g-role">
    <h2><span class="g-tag">Role</span>Accountant / Fee Clerk</h2>
    <p class="g-role-summary">You manage fee invoices and payments — you won't see student academic records like grades or attendance.</p>

    <h3>What you'll see</h3>
    <p>After logging in you'll land on the app-picker screen — click <strong>ERPNext</strong>. Use the search bar at the top (or the sidebar) and type <strong>Sales Invoice</strong> to see every fee invoice raised by the school, with its status.</p>

    <h3>Common tasks</h3>
    <ol class="g-steps">
      <li><strong>Find unpaid or overdue fees.</strong> Open <strong>Sales Invoice</strong>, then use the <strong>Status</strong> filter at the top of the list and choose "Unpaid" or "Overdue".</li>
      <li>
        <strong>Record a payment.</strong>
        <ol class="g-substeps">
          <li>Open the specific invoice from the list.</li>
          <li>Click <strong>Create</strong>, then <strong>Payment</strong> — this pre-fills the amount from the invoice.</li>
          <li>Check the amount and payment method, then click <strong>Save</strong>, then <strong>Submit</strong>.</li>
          <li>The invoice's status updates automatically to "Paid" (or stays "Unpaid" if it was only a partial payment).</li>
        </ol>
      </li>
      <li><strong>Create a new invoice.</strong> From the Sales Invoice list, click <strong>+ Add Sales Invoice</strong>, choose the student/customer, add the fee items, and <strong>Save</strong>, then <strong>Submit</strong>.</li>
      <li><strong>Set up a new term's fee plan.</strong> Look at <strong>Fee Structure</strong> for the program-wide plan, then <strong>Fee Schedule</strong> to generate the actual invoices for every student in that program at once.</li>
      <li><strong>Answer "has this family paid?"</strong> Search Sales Invoice by the student's name — every invoice for them shows up with its exact status.</li>
    </ol>
  </section>

  <section id="student" class="g-section g-role">
    <h2><span class="g-tag">Role</span>Student</h2>
    <p class="g-role-summary">You have your own simple portal — your timetable, your grades, your fees, and your attendance record. You never see the full desk staff use.</p>

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
      <li><strong>Forgot your password?</strong> Contact your office admin — they can reset it for you.</li>
      <li><strong>The blue banner at the top</strong> can be closed with the &times; on its right — it's just a welcome message and closing it doesn't affect anything else.</li>
      <li><strong>Every list in this system works the same way:</strong> click a row to open it, use the buttons at the top-right to add new records, edit, save, or submit.</li>
      <li><strong>"Save" vs "Submit":</strong> Save keeps a draft you can still edit. Submit locks it in as final/official — used for attendance, grades, and invoices. Submitted records need Cancel before they can be changed.</li>
      <li><strong>Still stuck?</strong> Contact your office admin for help.</li>
    </ol>
  </section>

  <footer class="g-footer">
    <p>{SCHOOL_NAME} &middot; this page needs no login and can be reached any time at <code>/school-guide</code>. Looking for the hospital module? See the <a href="/health-guide">Health Guide</a>.</p>
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
.g-back{ display: inline-block; margin-bottom: 18px; font-size: 13.5px; color: var(--navy); text-decoration: none; }
.g-back:hover{ text-decoration: underline; }
.g-hero{ text-align: center; padding: 12px 0 26px; border-bottom: 1px solid var(--border); margin-bottom: 22px; }
.g-crest{
  width: 56px; height: 56px; border-radius: 50%;
  background: var(--navy); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-family: Georgia, serif; font-weight: 700; font-size: 20px;
  margin: 0 auto 14px; border: 3px solid var(--marigold);
}
.g-eyebrow{ text-transform: uppercase; letter-spacing: .08em; font-size: 12px; color: var(--marigold); font-weight: 700; margin: 0 0 6px; }
.g-hero h1{ font-size: 30px; margin: 0 0 10px; }
.g-dek{ color: var(--charcoal); max-width: 50ch; margin: 0 auto; font-size: 15.5px; }

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

.g-glossary{
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
  margin: 16px 0 18px;
}
.g-gterm{
  background: var(--parchment); border: 1px solid var(--border); border-radius: 8px;
  padding: 12px 14px; font-size: 13.5px;
}
.g-gterm strong{ display: block; color: var(--navy-dark); margin-bottom: 4px; font-size: 14px; }
.g-gterm span{ color: var(--charcoal); }
@media (max-width: 620px){ .g-glossary{ grid-template-columns: 1fr; } }

.g-footer{
  border-top: 1px solid var(--border); margin-top: 30px; padding-top: 16px;
  text-align: center; font-size: 12.5px; color: var(--charcoal);
}
.g-footer a{ color: var(--navy); }

@media (max-width: 480px){
  .guide{ padding: 4px 2px 30px; }
  .g-hero h1{ font-size: 24px; }
}
"""


def ensure_guide_page():
    version_marker = f"<!-- school-guide-version:{PAGE_VERSION} -->"
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
        "title": "School Guide",
        "route": ROUTE,
        "published": 1,
        "content_type": "HTML",
        "main_section_html": full_html,
        "css": CSS_CONTENT,
        "full_width": 1,
        "show_title": 0,
        "show_sidebar": 0,
        "meta_title": f"School Guide — {SCHOOL_NAME}",
        "meta_description": "Deep, role-by-role guide to the school module — no login required to view.",
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
