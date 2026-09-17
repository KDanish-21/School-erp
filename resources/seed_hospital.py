"""
Idempotent demo-data seed for the Healthcare (Marley) module — same proven
pattern as seed_school.py, installed on the SAME site/Company (one desk,
one setup), not a separate site.

Confirmed the hard way (iterative local testing) — several Healthcare-app
gaps that aren't obvious from the doctype list alone:
  - Patient Appointment's `duration` field auto-fetches from
    `Appointment Type.default_duration` via `fetch_from` — if that's unset
    (0), appointment creation fails with "Appointment end must be after
    start" even when `duration` is set explicitly on the appointment
    itself, because the fetch overwrites it during validate().
  - Lab Test Template needs `lab_test_code` set explicitly — its own
    `after_insert()` auto-creates a linked Item using that field as the
    Item Code, and throws "Item Code is required" if it's blank, even
    though `lab_test_code` isn't itself a mandatory field on the template.
  - Lab Test requires `patient_sex` explicitly — it does not auto-fetch
    from the linked Patient.
  - Drug Prescription rows need `drug_code` (a real Link to Item) — a
    plain `drug_name` string alone is not enough; a Drug Item must exist
    first, same "pre-create the Item" pattern already used for Fee
    Category in seed_school.py.

Run with:
    cd ~/frappe-bench/sites
    ../env/bin/python ../seed_hospital.py
"""
import os
import random
from datetime import date, timedelta

import frappe
from faker import Faker

import brand

SITE_NAME = os.environ.get("SITE_NAME", "erp.localhost")
SITES_PATH = os.environ.get("SITES_PATH", "/Users/danishkhan/frappe-bench/sites")

frappe.init(site=SITE_NAME, sites_path=SITES_PATH)
frappe.connect()
frappe.set_user("Administrator")

COMPANY = brand.COMPANY_NAME  # reuse the exact same Company as the school — one setup
DEMO_PASSWORD = "Demo@1234"
HOSPITAL_DOMAIN = brand.HOSPITAL_DOMAIN
TODAY = date(2026, 9, 16)

fake = Faker("en_IN")

DEPARTMENTS = ["General Medicine", "Pediatrics", "Orthopedics", "Gynecology", "ENT", "Dermatology"]

DOCTORS = [
    ("Anand", "Verma", "General Medicine", "Male"),
    ("Kavita", "Rao", "Pediatrics", "Female"),
    ("Rajesh", "Menon", "Orthopedics", "Male"),
    ("Sunita", "Desai", "Gynecology", "Female"),
    ("Arjun", "Nair", "ENT", "Male"),
    ("Meera", "Kapoor", "Dermatology", "Female"),
    ("Vikram", "Singh", "General Medicine", "Male"),
    ("Neha", "Joshi", "Pediatrics", "Female"),
]
HERO_DOCTOR = "Anand Verma"  # General Medicine — used in the guide's examples

DRUGS = ["Paracetamol 500mg", "Amoxicillin 250mg", "Cetirizine 10mg", "Ibuprofen 400mg", "Omeprazole 20mg", "Vitamin D3"]

LAB_TEMPLATES = [
    ("Complete Blood Count", "CBC-001", 500),
    ("Blood Sugar (Fasting)", "FBS-001", 150),
    ("Urine Routine", "URE-001", 200),
    ("Lipid Profile", "LIP-001", 800),
]

PATIENT_COUNT = 60
HERO_PATIENT = None  # set once created, index 0


def log(msg):
    print(f"[hospital] {msg}")


def setup_departments():
    for dept in DEPARTMENTS:
        if not frappe.db.exists("Medical Department", dept):
            frappe.get_doc({"doctype": "Medical Department", "department": dept}).insert(ignore_permissions=True)
    frappe.db.commit()
    log(f"{len(DEPARTMENTS)} departments")


def ensure_role_profile(name, roles):
    if frappe.db.exists("Role Profile", name):
        rp = frappe.get_doc("Role Profile", name)
    else:
        rp = frappe.new_doc("Role Profile")
        rp.role_profile = name
    existing_roles = {r.role for r in rp.get("roles")}
    changed = False
    for role in roles:
        if role not in existing_roles:
            rp.append("roles", {"role": role})
            changed = True
    if rp.is_new() or changed:
        rp.save(ignore_permissions=True)
    return name


def ensure_user(email, first_name, last_name, role_profile=None, user_type="System User"):
    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
    else:
        user = frappe.new_doc("User")
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.user_type = user_type
        user.send_welcome_email = 0
    if role_profile:
        if role_profile not in [r.role_profile for r in user.get("role_profiles")]:
            user.append("role_profiles", {"role_profile": role_profile})
    user.new_password = DEMO_PASSWORD
    user.send_welcome_email = 0
    user.save(ignore_permissions=True)
    return user.name


def setup_doctors():
    # Healthcare Practitioner autonames to HLC-PRAC-<year>-#### — NOT the
    # person's name — so the display name ("Anand Verma") and the real doc
    # name used everywhere else (appointments, encounters) must be tracked
    # separately, confirmed the hard way via a LinkValidationError.
    by_full_name = {}
    for first, last, dept, sex in DOCTORS:
        full = f"{first} {last}"
        existing = frappe.db.exists("Healthcare Practitioner", {"first_name": first, "last_name": last})
        if existing:
            by_full_name[full] = existing
            continue
        email = f"{first.lower()}.{last.lower()}@{HOSPITAL_DOMAIN}"
        ensure_role_profile("Doctor", ["Physician"])
        user_name = ensure_user(email, first, last, role_profile="Doctor")
        prac = frappe.get_doc({
            "doctype": "Healthcare Practitioner",
            "first_name": first, "last_name": last,
            "department": dept, "gender": sex,
            "user_id": user_name,
        })
        prac.insert(ignore_permissions=True)
        by_full_name[full] = prac.name
    frappe.db.commit()
    log(f"{len(DOCTORS)} doctors")
    return by_full_name


def setup_service_units():
    # Healthcare Service Unit's own validate() unconditionally looks up
    # `service_unit_type` the moment it's not exactly "" (a genuinely unset
    # field is None, not "", so it still hits this branch) — confirmed the
    # hard way with "Healthcare Service Unit Type None not found". A real
    # type record + explicitly setting it is required, not optional.
    if not frappe.db.exists("Healthcare Service Unit Type", "Consultation Room"):
        frappe.get_doc({
            "doctype": "Healthcare Service Unit Type",
            "service_unit_type": "Consultation Room",
            "allow_appointments": 1,
        }).insert(ignore_permissions=True)

    # Autonames as "<healthcare_service_unit_name> - <Company Abbr>", not
    # the plain name given — confirmed the hard way via a duplicate-key
    # error once the idempotency check (wrongly comparing against the
    # un-suffixed name) let a second insert through. Look up by the field
    # value instead of assuming it equals `name`.
    units = []
    for dept in DEPARTMENTS:
        label = f"{dept} - Consultation Room"
        existing = frappe.db.exists("Healthcare Service Unit", {"healthcare_service_unit_name": label})
        if not existing:
            doc = frappe.get_doc({
                "doctype": "Healthcare Service Unit",
                "healthcare_service_unit_name": label,
                "service_unit_type": "Consultation Room",
                "company": COMPANY,
            })
            doc.insert(ignore_permissions=True)
            existing = doc.name
        units.append(existing)
    frappe.db.commit()
    log(f"{len(units)} service units")
    return units


def setup_appointment_type():
    name = "General Consultation"
    if not frappe.db.exists("Appointment Type", name):
        frappe.get_doc({
            "doctype": "Appointment Type",
            "appointment_type": name,
            "allow_booking_for": "Practitioner",
            "default_duration": 15,
        }).insert(ignore_permissions=True)
    else:
        # self-heal: this exact field is the gotcha documented above
        if not frappe.db.get_value("Appointment Type", name, "default_duration"):
            frappe.db.set_value("Appointment Type", name, "default_duration", 15)
    frappe.db.commit()
    log(f"Appointment Type '{name}'")
    return name


def setup_drug_items():
    for drug in DRUGS:
        if not frappe.db.exists("Item", drug):
            frappe.get_doc({
                "doctype": "Item", "item_code": drug, "item_name": drug,
                "item_group": "Drug", "stock_uom": "Nos", "is_stock_item": 0,
            }).insert(ignore_permissions=True)
    frappe.db.commit()
    log(f"{len(DRUGS)} drug items")


def setup_lab_templates():
    for name, code, rate in LAB_TEMPLATES:
        if not frappe.db.exists("Lab Test Template", name):
            frappe.get_doc({
                "doctype": "Lab Test Template",
                "lab_test_name": name, "lab_test_code": code,
                "department": "General Medicine", "lab_test_group": "Laboratory",
                "lab_test_template_type": "Single", "lab_test_rate": rate,
            }).insert(ignore_permissions=True)
        elif frappe.db.get_value("Lab Test Template", name, "department") not in DEPARTMENTS:
            # self-heal: an earlier throwaway manual test created this
            # template pointing at a department that no longer exists
            frappe.db.set_value("Lab Test Template", name, "department", "General Medicine")
    frappe.db.commit()
    log(f"{len(LAB_TEMPLATES)} lab test templates")


def setup_patients():
    global HERO_PATIENT
    names = frappe.get_all("Patient", filters={"first_name": ["!=", ""]}, pluck="name")
    if len(names) >= PATIENT_COUNT:
        HERO_PATIENT = names[0]
        log(f"{len(names)} patients already exist — skipping")
        return names

    created = []
    for i in range(PATIENT_COUNT):
        fake.seed_instance(3000 + i)
        sex = random.Random(3000 + i).choice(["Male", "Female"])
        first = fake.first_name_male() if sex == "Male" else fake.first_name_female()
        last = fake.last_name()
        if frappe.db.exists("Patient", {"first_name": first, "last_name": last}):
            created.append(f"{first} {last}")
            continue
        dob = date(random.Random(3000 + i).randint(1955, 2020), random.Random(4000 + i).randint(1, 12), random.Random(5000 + i).randint(1, 28))
        p = frappe.get_doc({
            "doctype": "Patient",
            "first_name": first, "last_name": last, "sex": sex,
            "dob": dob,
            "mobile": f"98{random.Random(6000 + i).randint(10000000, 99999999)}",
        })
        p.insert(ignore_permissions=True)
        created.append(p.name)
    frappe.db.commit()
    HERO_PATIENT = created[0] if created else None
    log(f"{len(created)} patients")
    return created


def setup_front_desk_and_lab_users():
    ensure_role_profile("Front Desk", ["Healthcare Administrator"])
    ensure_user(f"reception@{HOSPITAL_DOMAIN}", "Priya", "Iyer", role_profile="Front Desk")
    ensure_role_profile("Nurse", ["Nursing User"])
    ensure_user(f"nurse.fernandes@{HOSPITAL_DOMAIN}", "Lisa", "Fernandes", role_profile="Nurse")
    ensure_role_profile("Lab Technician", ["Laboratory User"])
    ensure_user(f"lab.iyer@{HOSPITAL_DOMAIN}", "Sanjay", "Iyer", role_profile="Lab Technician")
    frappe.db.commit()
    log("Front desk, nurse, and lab technician users")


# 30-minute slots, 9am-1pm and 2-5:30pm (skips a lunch hour) — used to
# assign each practitioner's Nth appointment of the day a *guaranteed*
# non-overlapping time by construction, rather than hoping a randomly
# chosen time doesn't collide. Confirmed the hard way that leaving it to
# chance (a small pool of random times) made reruns non-idempotent: the
# app's own overlap check depends on the full DB state, not just this
# run's insert order, so a collision that failed in one run could
# silently succeed or fail differently on the next.
SLOT_TIMES = [
    "09:00:00", "09:30:00", "10:00:00", "10:30:00", "11:00:00", "11:30:00", "12:00:00", "12:30:00",
    "14:00:00", "14:30:00", "15:00:00", "15:30:00", "16:00:00", "16:30:00", "17:00:00", "17:30:00",
]


def _slot_time(nth_for_practitioner_today):
    return SLOT_TIMES[nth_for_practitioner_today % len(SLOT_TIMES)]


def setup_appointments_and_encounters(doctor_by_full_name, patients):
    doc_by_dept = {}
    for first, last, dept, _sex in DOCTORS:
        doc_by_dept.setdefault(dept, []).append(doctor_by_full_name[f"{first} {last}"])

    appt_count = 0
    enc_count = 0
    lab_count = 0

    # Past week: mostly Closed (with a consultation), a few Cancelled/No Show
    #
    # Each slot gets its OWN Random instance seeded by its own fixed index,
    # not a Random shared across a day's slots — confirmed the hard way
    # that sharing one made reruns non-idempotent: an early "already exists"
    # `continue` skips that slot's rng calls, desyncing every later slot's
    # sequence from what the first run produced, so a rerun quietly created
    # a different set of "new" appointments instead of recognizing the same
    # ones. Same class of bug the Faker per-record seeding in seed_school.py
    # was already written to avoid.
    for day_offset in range(6, 0, -1):
        appt_date = TODAY - timedelta(days=day_offset)
        practitioner_slot_count = {}
        for slot in range(5):
            rng = random.Random(7000 + day_offset * 10 + slot)
            dept = rng.choice(DEPARTMENTS)
            practitioner = rng.choice(doc_by_dept[dept])
            patient = rng.choice(patients)
            existing = frappe.db.exists("Patient Appointment", {
                "patient": patient, "practitioner": practitioner, "appointment_date": appt_date,
            })
            nth = practitioner_slot_count.get(practitioner, 0)
            practitioner_slot_count[practitioner] = nth + 1
            if existing:
                appt_count += 1
                continue
            outcome = rng.random()
            status = "Cancelled" if outcome < 0.12 else ("Closed" if outcome < 0.85 else None)  # else -> auto No Show
            appt = frappe.get_doc({
                "doctype": "Patient Appointment",
                "patient": patient, "practitioner": practitioner,
                "appointment_type": "General Consultation", "appointment_for": "Practitioner",
                "department": dept, "company": COMPANY,
                "appointment_date": appt_date, "appointment_time": _slot_time(nth),
            })
            if status:
                appt.status = status
            try:
                appt.insert(ignore_permissions=True)
            except frappe.exceptions.ValidationError:
                # belt-and-suspenders: the deterministic per-practitioner
                # slot assignment above should already prevent overlaps,
                # but skip rather than crash if some other validation
                # (e.g. a patient-side conflict) still rejects it.
                frappe.db.rollback()
                continue
            appt_count += 1

            if status == "Closed":
                enc = frappe.get_doc({
                    "doctype": "Patient Encounter",
                    "patient": patient, "practitioner": practitioner,
                    "encounter_date": appt_date, "encounter_time": appt.appointment_time,
                    "appointment_type": "General Consultation", "company": COMPANY,
                    "appointment": appt.name,
                    "drug_prescription": [{
                        "drug_code": rng.choice(DRUGS), "dosage_form": "Tablet",
                        "dosage": rng.choice(["1-0-1", "1-1-1", "0-0-1"]), "period": rng.choice(["3 Day", "5 Day", "1 Week"]),
                    }],
                })
                enc.insert(ignore_permissions=True)
                enc_count += 1

                vitals = frappe.get_doc({
                    "doctype": "Vital Signs",
                    "naming_series": "HLC-VTS-.YYYY.-",
                    "patient": patient, "encounter": enc.name,
                    "signs_date": appt_date, "signs_time": appt.appointment_time,
                    "temperature": round(rng.uniform(97.5, 99.8), 1),
                    "pulse": rng.randint(65, 95),
                    "bp_systolic": rng.randint(105, 135), "bp_diastolic": rng.randint(70, 88),
                })
                vitals.insert(ignore_permissions=True)

                if rng.random() < 0.3:
                    template_name = rng.choice(LAB_TEMPLATES)[0]
                    sex = frappe.db.get_value("Patient", patient, "sex")
                    lt = frappe.get_doc({
                        "doctype": "Lab Test", "template": template_name,
                        "patient": patient, "patient_sex": sex, "company": COMPANY,
                        "practitioner": practitioner,
                    })
                    lt.insert(ignore_permissions=True)
                    if rng.random() < 0.6:
                        lt.db_set("status", "Approved")
                    lab_count += 1

            # Commit per appointment (not once at the end of the whole
            # function) — this loop can produce 1000+ row operations across
            # Patient Appointment/Encounter/Vital Signs/Lab Test and their
            # child tables, and a single giant transaction here is exactly
            # what got fully rolled back by a mariadbd crash/OOM restart on
            # a memory-constrained deploy, wiping all prior progress in this
            # function at once. Committing per-record means a crash loses at
            # most the one record in flight, and the idempotency checks above
            # let a retry pick up right where it left off.
            frappe.db.commit()

    # Next few days: Scheduled/Open, no consultation yet
    for day_offset in range(1, 6):
        appt_date = TODAY + timedelta(days=day_offset)
        practitioner_slot_count = {}
        for slot in range(3):
            rng = random.Random(8000 + day_offset * 10 + slot)  # per-slot seed, same reasoning as above
            dept = rng.choice(DEPARTMENTS)
            practitioner = rng.choice(doc_by_dept[dept])
            patient = rng.choice(patients)
            nth = practitioner_slot_count.get(practitioner, 0)
            practitioner_slot_count[practitioner] = nth + 1
            if frappe.db.exists("Patient Appointment", {"patient": patient, "practitioner": practitioner, "appointment_date": appt_date}):
                appt_count += 1
                continue
            try:
                frappe.get_doc({
                    "doctype": "Patient Appointment",
                    "patient": patient, "practitioner": practitioner,
                    "appointment_type": "General Consultation", "appointment_for": "Practitioner",
                    "department": dept, "company": COMPANY,
                    "appointment_date": appt_date, "appointment_time": _slot_time(nth),
                }).insert(ignore_permissions=True)
            except frappe.exceptions.ValidationError:
                frappe.db.rollback()
                continue
            appt_count += 1
            frappe.db.commit()

    log(f"{appt_count} appointments, {enc_count} consultations, {lab_count} lab tests")


def setup_inpatients(patients):
    rng = random.Random(9000)
    admitted_patient = patients[10]
    discharged_patient = patients[20]

    if not frappe.db.exists("Inpatient Record", {"patient": admitted_patient}):
        rec = frappe.get_doc({
            "doctype": "Inpatient Record",
            "patient": admitted_patient,
            "scheduled_date": TODAY - timedelta(days=2),
        })
        rec.insert(ignore_permissions=True)
        rec.db_set("status", "Admitted")

    if not frappe.db.exists("Inpatient Record", {"patient": discharged_patient}):
        rec = frappe.get_doc({
            "doctype": "Inpatient Record",
            "patient": discharged_patient,
            "scheduled_date": TODAY - timedelta(days=5),
        })
        rec.insert(ignore_permissions=True)
        rec.db_set("status", "Discharged")

    frappe.db.commit()
    log("2 inpatient admissions (1 admitted, 1 discharged)")


def run_all():
    setup_departments()
    setup_appointment_type()
    setup_drug_items()
    setup_lab_templates()
    doctor_by_full_name = setup_doctors()
    setup_service_units()
    setup_front_desk_and_lab_users()
    patients = setup_patients()
    setup_appointments_and_encounters(doctor_by_full_name, patients)
    setup_inpatients(patients)
    frappe.db.commit()
    log("Done.")


if __name__ == "__main__":
    run_all()
    frappe.db.commit()
