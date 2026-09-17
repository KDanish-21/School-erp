"""
Publishes a deep, plain-language guide for the HEALTH (hospital) module
only, at /health-guide — no login required to view. Companion to
school_guide.py and guide.py (a small landing page linking to both).

Run with:
    cd ~/frappe-bench/sites
    ../env/bin/python ../health_guide.py
"""
import os

import frappe

import brand

SITE_NAME = os.environ.get("SITE_NAME", "erp.localhost")
SITES_PATH = os.environ.get("SITES_PATH", "/Users/danishkhan/frappe-bench/sites")

frappe.init(site=SITE_NAME, sites_path=SITES_PATH)
frappe.connect()
frappe.set_user("Administrator")

ROUTE = "health-guide"
PAGE_VERSION = "2"


def log(msg):
    print(f"[health-guide] {msg}")


HTML_CONTENT = f"""
<div class="guide">

  <a class="g-back" href="/guide">&larr; All guides</a>

  <header class="g-hero">
    <div class="g-crest hg-crest">+</div>
    <p class="g-eyebrow">{brand.HOSPITAL_NAME}</p>
    <h1>The Health Guide</h1>
    <p class="g-dek">Everything about running the hospital module on this system — how it's organized, what each role does, and every common task explained step by step.</p>
  </header>

  <nav class="g-jump" aria-label="Jump to your role">
    <span class="g-jump-label">I am a&hellip;</span>
    <a href="#hospitaladmin">Hospital Admin</a>
    <a href="#doctor">Doctor</a>
    <a href="#nurse">Nurse</a>
    <a href="#frontdesk">Front Desk</a>
    <a href="#labtech">Lab Technician</a>
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
      <p>After logging in you may briefly see a screen with a few icons (<em>ERPNext</em>, <em>Education</em>, <em>Marley Health</em>, <em>Framework</em>). Click <strong>Marley Health</strong> — that's the hospital side of the system, which we call <strong>{brand.HOSPITAL_NAME}</strong> everywhere else in this guide. (The tile itself still shows the underlying software's real name — that's the open-source app this module runs on, not something we relabel.)</p>
    </div>
  </section>

  <section id="concepts" class="g-section">
    <h2><span class="g-tag">Before you start</span>How the hospital side is organized</h2>
    <p class="g-role-summary">The names in this system have been simplified from the stock medical software terms — here's what everything actually means, and how the pieces connect for one patient's visit.</p>
    <div class="g-glossary">
      <div class="g-gterm"><strong>Patient</strong><span>One record per person — their name, date of birth, contact details, and their whole visit history lives here.</span></div>
      <div class="g-gterm"><strong>Doctor</strong><span>A practitioner's record — which department they're in, and every appointment/consultation tied to them. (Internally still called "Healthcare Practitioner".)</span></div>
      <div class="g-gterm"><strong>Patient Appointment</strong><span>A booked visit — patient, doctor, date and time. This is what Front Desk creates.</span></div>
      <div class="g-gterm"><strong>Consultation</strong><span>The actual write-up of a visit once it happens — symptoms, diagnosis, prescriptions, and lab orders all get attached here. (Internally "Patient Encounter".)</span></div>
      <div class="g-gterm"><strong>Room / Ward</strong><span>A physical space in the hospital — a consultation room, a ward bed, etc. (Internally "Healthcare Service Unit".)</span></div>
      <div class="g-gterm"><strong>Admission</strong><span>A patient staying in the hospital rather than an outpatient visit — has its own status (scheduled, admitted, discharged). (Internally "Inpatient Record".)</span></div>
      <div class="g-gterm"><strong>Lab Test</strong><span>A single test ordered for a patient, tied back to the Consultation that ordered it via its "Ordered From" field.</span></div>
      <div class="g-gterm"><strong>Free Follow-up Pass</strong><span>A time-limited window where a patient can return to the same doctor without being charged again. (Internally "Fee Validity".)</span></div>
    </div>
    <div class="g-note">
      <p><strong>A typical visit, start to finish:</strong> Front Desk registers the <strong>Patient</strong> and books a <strong>Patient Appointment</strong> → the <strong>Doctor</strong> sees them and writes a <strong>Consultation</strong> → the Consultation may include a drug prescription and/or a <strong>Lab Test</strong> order → the Lab Technician enters the result → if needed, the patient becomes an <strong>Admission</strong>.</p>
    </div>
  </section>

  <section id="hospitaladmin" class="g-section g-role">
    <h2><span class="g-tag">Role</span>Hospital Admin</h2>
    <p class="g-role-summary">You see everything across the hospital — every patient, every doctor, every appointment and admission. Nothing is hidden from this role.</p>

    <h3>What you'll see</h3>
    <p>After clicking <strong>Marley Health</strong>, you land on the Healthcare dashboard: a live chart of appointments by department, four headline numbers (Total Patients, Total Patients Admitted, Open Appointments, Appointments to Bill), and shortcuts to Patient Appointment, Patient, Rooms &amp; Wards, Doctors, Patient History, and the Dashboard. Below that, "Reports &amp; Masters" groups the full system: Masters, Outpatient, Orders, Inpatient, Diagnostics, Insurance, and more.</p>

    <h3>Common tasks</h3>
    <ol class="g-steps">
      <li><strong>Check overall load.</strong> The chart on the home dashboard shows appointments by department, split by status (Open, Scheduled, Closed, Cancelled) — a quick read on where the hospital is busy.</li>
      <li><strong>See every doctor and their department.</strong> Click <strong>Doctors</strong> to see the full list with status (Active/Disabled).</li>
      <li><strong>Check who's currently admitted.</strong> Click <strong>Admission</strong> in the sidebar — every current inpatient and their room/ward.</li>
      <li><strong>Review the appointment book across the hospital.</strong> Open <strong>Patient Appointment</strong> and filter by date or department to see the full schedule, not just one doctor's.</li>
      <li><strong>Manage rooms/wards.</strong> Click <strong>Rooms &amp; Wards</strong> to add a new one or check occupancy.</li>
      <li><strong>Add or adjust staff access.</strong> Open the <strong>User</strong> list (search for it in the top bar), find the staff member, and check their Role Profile — this controls what they can see (Doctor, Nurse, Front Desk, or Lab Technician).</li>
    </ol>
    <div class="g-note">
      <p><strong>This role can do everything below too</strong> — Doctor, Nurse, Front Desk, and Lab Technician tasks are all reachable from the same login.</p>
    </div>
  </section>

  <section id="doctor" class="g-section g-role">
    <h2><span class="g-tag">Role</span>Doctor</h2>
    <p class="g-role-summary">You see your own patients — your appointments, consultations, and the prescriptions and lab orders you've written.</p>

    <h3>What you'll see</h3>
    <p>The same Healthcare dashboard, with your own shortcuts front and center: Patient Appointment, Patient, Rooms &amp; Wards, and Doctors.</p>

    <h3>Common tasks</h3>
    <ol class="g-steps">
      <li><strong>Check today's appointments.</strong> Click <strong>Patient Appointment</strong>, then filter by today's date — each row shows the patient and the time.</li>
      <li>
        <strong>See a patient and write up the visit.</strong>
        <ol class="g-substeps">
          <li>Open the patient's appointment, or click <strong>Consultation</strong> in the sidebar and <strong>+ Add</strong> a new one.</li>
          <li>Choose the patient — their past visits, vitals, and prescriptions are all on their record if you need history.</li>
          <li>Add a drug prescription and/or a lab order from the same screen if needed.</li>
          <li>Click <strong>Save</strong>, then <strong>Submit</strong> once the consultation is complete.</li>
        </ol>
      </li>
      <li><strong>Order a lab test.</strong> From the patient's Consultation, add a test under "Lab Tests" — the lab technician sees it appear on their side automatically, and it shows "Ordered From" pointing back to this consultation.</li>
      <li><strong>Prescribe medication.</strong> On the same Consultation, add a row under "Drug Prescription" — choose the drug, dosage, and how long it should be taken.</li>
      <li><strong>Look up a patient's full history before seeing them.</strong> Open <strong>Patient History</strong> (a shortcut on the dashboard) — every past consultation, prescription, and lab result for that patient in one place.</li>
      <li><strong>Admit a patient.</strong> From the patient's record or Consultation, there's an option to create an Admission if they need to stay rather than go home.</li>
    </ol>
  </section>

  <section id="nurse" class="g-section g-role">
    <h2><span class="g-tag">Role</span>Nurse</h2>
    <p class="g-role-summary">You manage ward patients — admissions, vitals, and day-to-day inpatient care.</p>

    <h3>What you'll see</h3>
    <p>The same Healthcare dashboard as everyone else, scoped to your ward duties — Admissions and Patient records are where you'll spend most of your time.</p>

    <h3>Common tasks</h3>
    <ol class="g-steps">
      <li><strong>Check who's admitted.</strong> Click <strong>Admission</strong> in the sidebar to see every current inpatient and which room/ward they're in, and their status (Admitted, Discharge Scheduled, Discharged).</li>
      <li><strong>Record a patient's vitals.</strong> Open the patient's record or their current Consultation, add a new Vital Signs entry (temperature, pulse, blood pressure), and <strong>Save</strong>.</li>
      <li><strong>Check a room/ward's status.</strong> Click <strong>Rooms &amp; Wards</strong> to see which are occupied.</li>
      <li><strong>Prepare a patient for discharge.</strong> Open their Admission record and update the status as the doctor signs off — this keeps the room/ward occupancy accurate for the next patient.</li>
    </ol>
  </section>

  <section id="frontdesk" class="g-section g-role">
    <h2><span class="g-tag">Role</span>Front Desk</h2>
    <p class="g-role-summary">You register patients and manage the appointment book — you won't see clinical details like consultations or prescriptions.</p>

    <h3>What you'll see</h3>
    <p>The Healthcare dashboard with Patient and Patient Appointment front and center — this is your main working screen all day.</p>

    <h3>Common tasks</h3>
    <ol class="g-steps">
      <li><strong>Register a new patient.</strong> Click <strong>Patient</strong>, then <strong>+ Add Patient</strong>. Fill in their name, date of birth, sex, and contact details, then <strong>Save</strong>.</li>
      <li>
        <strong>Book an appointment.</strong>
        <ol class="g-substeps">
          <li>Click <strong>Patient Appointment</strong>, then <strong>New</strong>.</li>
          <li>Choose the patient and the doctor.</li>
          <li>Pick a date and time, and <strong>Save</strong>.</li>
        </ol>
      </li>
      <li><strong>Find a patient's upcoming visit.</strong> Open <strong>Patient Appointment</strong> and filter by patient name or date.</li>
      <li><strong>Reschedule or cancel a visit.</strong> Open the appointment and change its date/time, or change its status to Cancelled.</li>
      <li><strong>Check whether a patient already exists</strong> before creating a duplicate — search <strong>Patient</strong> by name or mobile number first.</li>
    </ol>
  </section>

  <section id="labtech" class="g-section g-role">
    <h2><span class="g-tag">Role</span>Lab Technician</h2>
    <p class="g-role-summary">You process lab orders and enter results — you won't see appointments or consultations.</p>

    <h3>What you'll see</h3>
    <p>Click <strong>Lab Test</strong> in the sidebar to see every test ordered by a doctor, in order of when it was requested.</p>

    <h3>Common tasks</h3>
    <ol class="g-steps">
      <li><strong>Find pending tests.</strong> Open <strong>Lab Test</strong> and filter by <strong>Status = Draft</strong> — these are ordered but not yet completed.</li>
      <li><strong>Enter a result.</strong> Open the test, fill in the result value(s), then click <strong>Save</strong>. Change the status to <strong>Completed</strong> once done, or <strong>Approved</strong> if a second sign-off is required.</li>
      <li><strong>See which visit ordered a test.</strong> Every Lab Test shows <strong>Ordered From</strong> — the consultation it came from — if you need the context.</li>
      <li><strong>Check what test to run.</strong> Each Lab Test links to a <strong>Lab Test Template</strong> (e.g. Complete Blood Count, Blood Sugar) that defines what's being measured.</li>
    </ol>
  </section>

  <section id="help" class="g-section">
    <h2><span class="g-tag">Good to know</span>General tips</h2>
    <ol class="g-steps">
      <li><strong>To log out:</strong> click your name in the bottom-left corner of the sidebar, then <strong>Logout</strong>.</li>
      <li><strong>Forgot your password?</strong> Contact your office admin — they can reset it for you.</li>
      <li><strong>The blue banner at the top</strong> can be closed with the &times; on its right — it's just a welcome message and closing it doesn't affect anything else.</li>
      <li><strong>Every list in this system works the same way:</strong> click a row to open it, use the buttons at the top-right to add new records, edit, save, or submit.</li>
      <li><strong>"Save" vs "Submit":</strong> Save keeps a draft you can still edit. Submit locks it in as final/official — used for consultations and lab tests. Submitted records need Cancel before they can be changed.</li>
      <li><strong>Some terms here differ from the stock software:</strong> if you ever see "Patient Encounter", "Healthcare Practitioner", "Healthcare Service Unit", "Fee Validity", "Inpatient Record", or a "Prescription" field on a Lab Test — those are the same things as Consultation, Doctor, Room/Ward, Free Follow-up Pass, Admission, and Ordered From described above, just under their original technical names (this can show up in error messages or older reports).</li>
      <li><strong>Still stuck?</strong> Contact your office admin for help.</li>
    </ol>
  </section>

  <footer class="g-footer">
    <p>{brand.HOSPITAL_NAME} &middot; this page needs no login and can be reached any time at <code>/health-guide</code>. Looking for the school module? See the <a href="/school-guide">School Guide</a>.</p>
  </footer>

</div>
"""

CSS_CONTENT = """
.guide{
  --navy: #172554;
  --navy-dark: #0B1120;
  --accent: #4D5565;
  --charcoal: #222326;
  --bg-light: #F4F5F8;
  --border: #DDE1EA;
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
  margin: 0 auto 14px; border: 3px solid var(--accent);
}
.hg-crest{ background: var(--navy); border-color: var(--accent); font-size: 28px; }
.g-eyebrow{ text-transform: uppercase; letter-spacing: .08em; font-size: 12px; color: var(--accent); font-weight: 700; margin: 0 0 6px; }
.g-hero h1{ font-size: 30px; margin: 0 0 10px; }
.g-dek{ color: var(--charcoal); max-width: 50ch; margin: 0 auto; font-size: 15.5px; }

.g-jump{
  display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
  justify-content: center; margin-bottom: 34px;
}
.g-jump-label{ font-size: 13px; color: var(--charcoal); margin-right: 4px; }
.g-jump a{
  font-size: 13.5px; text-decoration: none; color: var(--navy);
  border: 1px solid var(--border); background: var(--bg-light);
  padding: 6px 13px; border-radius: 999px;
}
.g-jump a:hover{ background: var(--navy); color: #fff; border-color: var(--navy); }

.g-section{ margin-bottom: 40px; }
.g-section h2{
  font-size: 21px; margin: 0 0 4px; display: flex; align-items: center; gap: 10px;
}
.g-tag{
  font-family: -apple-system, sans-serif; text-transform: uppercase; letter-spacing: .06em;
  font-size: 10.5px; font-weight: 700; color: #fff; background: var(--accent);
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
  background: var(--bg-light); border-left: 3px solid var(--accent);
  border-radius: 0 8px 8px 0; padding: 10px 16px; margin: 12px 0 16px;
  font-size: 14.5px;
}
.g-note p{ margin: 0; }
.guide code{
  background: var(--bg-light); border: 1px solid var(--border);
  padding: 1px 6px; border-radius: 4px; font-size: .92em;
}

.g-glossary{
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
  margin: 16px 0 18px;
}
.g-gterm{
  background: var(--bg-light); border: 1px solid var(--border); border-radius: 8px;
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
    version_marker = f"<!-- health-guide-version:{PAGE_VERSION} -->"
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
        "title": "Health Guide",
        "route": ROUTE,
        "published": 1,
        "content_type": "HTML",
        "main_section_html": full_html,
        "css": CSS_CONTENT,
        "full_width": 1,
        "show_title": 0,
        "show_sidebar": 0,
        "meta_title": f"Health Guide — {brand.HOSPITAL_NAME}",
        "meta_description": "Deep, role-by-role guide to the hospital module — no login required to view.",
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
