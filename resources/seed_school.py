"""
Demo data + role/dashboard setup for "Little Scholars Public School"
(Education app on top of ERPNext, site erp.localhost).

Safe to re-run: every creator function checks for an existing record
first. Only the time-relative sections (attendance / fee invoices /
payments) have their own idempotency keys.

Run with:
    cd ~/frappe-bench
    ./env/bin/python seed_school.py
"""
import random
from datetime import date, timedelta

import frappe
from faker import Faker

import os

SITE_NAME = os.environ.get("SITE_NAME", "erp.localhost")
SITES_PATH = os.environ.get("SITES_PATH", "/Users/danishkhan/frappe-bench/sites")

frappe.init(site=SITE_NAME, sites_path=SITES_PATH)
frappe.connect()
frappe.set_user("Administrator")

random.seed(42)
Faker.seed(42)
fake = Faker("en_IN")

# ---------------------------------------------------------------- constants

COMPANY = "Danish"
SCHOOL_ABBR = "LSPS"
SCHOOL_DOMAIN = "littlescholars.edu.in"
DEMO_PASSWORD = "Demo@1234"

ACADEMIC_YEAR = "2026-2027"
YEAR_START, YEAR_END = date(2026, 4, 1), date(2027, 3, 31)
TERM1_START, TERM1_END = date(2026, 4, 1), date(2026, 9, 30)
TERM2_START, TERM2_END = date(2026, 10, 1), date(2027, 3, 31)
TERM1_NAME = f"{ACADEMIC_YEAR} (Term 1)"
TERM2_NAME = f"{ACADEMIC_YEAR} (Term 2)"

TODAY = date(2026, 9, 11)
WEEK_MONDAY = TODAY - timedelta(days=TODAY.weekday())  # Mon of the current week
ASSESS_MONDAY = TODAY - timedelta(days=21) - timedelta(days=(TODAY - timedelta(days=21)).weekday())

GRADES = list(range(1, 7))                      # Class 1..6
SECTIONS = ["Section A", "Section B"]
GROUP_KEYS = [(g, s) for g in GRADES for s in SECTIONS]   # 12, in stable order
COURSES = ["English", "Hindi", "Mathematics", "Science", "Social Studies",
           "Computer Science", "Art", "Physical Education"]
EXAM_COURSES = ["English", "Mathematics", "Science", "Social Studies"]
STUDENTS_PER_GROUP = 10

PERIODS = [("09:00:00", "09:40:00"), ("09:40:00", "10:20:00"),
           ("10:35:00", "11:15:00"), ("11:15:00", "11:55:00"),
           ("13:00:00", "13:40:00"), ("13:40:00", "14:20:00")]

# hero logins (must line up with a specific group so User Permission scoping is demoable)
HERO_TEACHERS = {4: ("Rohan Mehta", "rohan.mehta@" + SCHOOL_DOMAIN)}     # group idx 4 = Class 3 - Section A
HERO_TEACHERS[9] = ("Priya Nair", "priya.nair@" + SCHOOL_DOMAIN)        # group idx 9 = Class 5 - Section B
HERO_STUDENTS = {2: ("Aditi", "Sharma", "aditi.sharma.s1@" + SCHOOL_DOMAIN)}   # group idx 2 = Class 2 - Section A
HERO_STUDENTS[11] = ("Kabir", "Malhotra", "kabir.malhotra.s1@" + SCHOOL_DOMAIN)  # group idx 11 = Class 6 - Section B


def log(msg):
    print(f"[seed] {msg}")


def group_name(idx):
    g, s = GROUP_KEYS[idx]
    return f"Class {g} - {s}"


# ---------------------------------------------------------- 1. calendar / grading

def setup_academic_calendar():
    if not frappe.db.exists("Academic Year", ACADEMIC_YEAR):
        frappe.get_doc({
            "doctype": "Academic Year", "academic_year_name": ACADEMIC_YEAR,
            "year_start_date": YEAR_START, "year_end_date": YEAR_END,
        }).insert(ignore_permissions=True)
        log(f"Academic Year {ACADEMIC_YEAR}")

    for name, start, end in ((TERM1_NAME, TERM1_START, TERM1_END), (TERM2_NAME, TERM2_START, TERM2_END)):
        if not frappe.db.exists("Academic Term", name):
            frappe.get_doc({
                "doctype": "Academic Term", "academic_year": ACADEMIC_YEAR,
                "term_name": name.split("(")[1].rstrip(")"),
                "term_start_date": start, "term_end_date": end,
            }).insert(ignore_permissions=True)
            log(f"Academic Term {name}")

    settings = frappe.get_single("Education Settings")
    settings.current_academic_year = ACADEMIC_YEAR
    settings.current_academic_term = TERM1_NAME
    settings.school_college_name_abbreviation = SCHOOL_ABBR
    settings.user_creation_skip = 1
    settings.save(ignore_permissions=True)


def setup_company_and_fiscal_year():
    # On the local dev bench this was done interactively by ERPNext's setup
    # wizard. A site created headlessly via `bench new-site` skips all of
    # that — not just the Company/Fiscal Year, but a batch of prerequisite
    # fixtures (Warehouse Type, Designation, UOM data, etc.) that Company
    # creation itself depends on (confirmed the hard way: creating a Company
    # directly threw "Could not find Warehouse Type: Transit", since that's
    # normally provisioned by the wizard's own fixture installer first).
    # Calling ERPNext's actual wizard functions directly is safer than
    # hand-rolling a subset — it's the exact same code path a real
    # interactive setup runs, so nothing else gets missed either.
    from erpnext.setup.setup_wizard.operations.install_fixtures import (
        install, install_company, install_defaults, get_fy_details,
    )
    from frappe.desk.page.setup_wizard.install_fixtures import install as frappe_install_fixtures

    args = frappe._dict({
        "company_name": COMPANY,
        "company_abbr": "D",
        "currency": "INR",
        "country": "India",
        "chart_of_accounts": "India - Chart of Accounts",
        "domain": "Education",
        "fy_start_date": YEAR_START,
        "fy_end_date": YEAR_END,
    })

    if not frappe.db.exists("Company", COMPANY):
        # Frappe's own wizard step (Gender, Salutation, etc.) runs before
        # ERPNext's — confirmed needed the hard way too: student creation
        # failed on "Could not find Gender: Male" without this.
        frappe_install_fixtures()
        install(country="India")
        install_company(args)
        log(f"Company {COMPANY} + Fiscal Year {get_fy_details(YEAR_START, YEAR_END)} created via ERPNext's own wizard fixtures")

    # Deliberately NOT nested inside the "Company doesn't exist yet" guard
    # above: an earlier interrupted run (crashed on a later missing-fixture
    # error) can leave Company already created but this step never reached —
    # confirmed the hard way. Guard on the Price List itself instead, so a
    # resumed run still fills this gap in.
    if not frappe.db.exists("Price List", "Standard Selling"):
        # Price Lists (Standard Selling/Buying) + Global Defaults + default
        # currency enablement + Stock Settings — also wizard-only, also
        # confirmed missing the hard way ("Could not find Default Price
        # List: Standard Selling", thrown deep into fee invoice generation).
        install_defaults(args)
        log("Price Lists + Global Defaults installed via ERPNext's wizard fixtures")

    frappe.db.commit()


def fix_student_role_desk_access():
    # education/install.py intends the Student role to be desk_access=0 (portal-only),
    # but only sets that when it creates the role fresh — if "Student" already existed
    # with the Frappe default of desk_access=1 (e.g. from an earlier partial install),
    # every portal Student ends up promoted to "System User" on save via
    # User.set_system_user()/has_desk_access(). Fix it at the source.
    if frappe.db.exists("Role", "Student"):
        role = frappe.get_doc("Role", "Student")
        if role.desk_access:
            role.desk_access = 0
            role.save(ignore_permissions=True)
            log("Fixed Student role desk_access -> 0")


def setup_holiday_list():
    name = f"{ACADEMIC_YEAR} School Holidays"
    if not frappe.db.exists("Holiday List", name):
        hl = frappe.get_doc({
            "doctype": "Holiday List", "holiday_list_name": name,
            "from_date": YEAR_START, "to_date": YEAR_END, "weekly_off": "Sunday",
        })
        hl.insert(ignore_permissions=True)
        hl.get_weekly_off_dates()
        hl.save(ignore_permissions=True)
    company = frappe.get_doc("Company", COMPANY)
    if company.default_holiday_list != name:
        company.default_holiday_list = name
        company.save(ignore_permissions=True)
    log(f"Holiday List {name} set as Company default")
    return name


def setup_grading_scale():
    name = "School Grading Scale"
    if frappe.db.exists("Grading Scale", name):
        return name
    gs = frappe.new_doc("Grading Scale")
    gs.grading_scale_name = name
    for grade, threshold in (("A", 80), ("B", 70), ("C", 60), ("D", 50), ("F", 0)):
        gs.append("intervals", {"grade_code": grade, "threshold": threshold})
    gs.insert(ignore_permissions=True)
    gs.submit()
    log(f"Grading Scale {name}")
    return name


# ---------------------------------------------------------- 2. rooms / batches / programs / courses

def setup_rooms():
    rooms = []
    for idx in range(len(GROUP_KEYS)):
        room_label = f"Room {101 + idx}"
        existing = frappe.db.get_value("Room", {"room_name": room_label}, "name")
        if not existing:
            doc = frappe.get_doc({"doctype": "Room", "room_name": room_label})
            doc.insert(ignore_permissions=True)
            existing = doc.name
        rooms.append(existing)
    log(f"{len(rooms)} rooms")
    return rooms


def setup_batches():
    for section in SECTIONS:
        if not frappe.db.exists("Student Batch Name", section):
            frappe.get_doc({"doctype": "Student Batch Name", "batch_name": section}).insert(ignore_permissions=True)
    log("Student Batch Names")


def setup_programs():
    programs = []
    for g in GRADES:
        name = f"Class {g}"
        if not frappe.db.exists("Program", name):
            frappe.get_doc({"doctype": "Program", "program_name": name}).insert(ignore_permissions=True)
        programs.append(name)
    log(f"{len(programs)} programs")
    return programs


def setup_courses():
    courses = []
    for c in COURSES:
        if not frappe.db.exists("Course", c):
            frappe.get_doc({"doctype": "Course", "course_name": c}).insert(ignore_permissions=True)
        courses.append(c)
    # wire all courses onto every program (Program.courses child table)
    for g in GRADES:
        prog = frappe.get_doc("Program", f"Class {g}")
        existing = {row.course for row in prog.courses}
        changed = False
        for c in courses:
            if c not in existing:
                prog.append("courses", {"course": c})
                changed = True
        if changed:
            prog.save(ignore_permissions=True)
    log(f"{len(courses)} courses, wired to programs")
    return courses


# ---------------------------------------------------------- 3. instructors

def setup_instructors():
    """Names are derived from a per-index seeded Faker instance so they are
    stable across separate script runs no matter what else (frappe internals,
    other random/Faker calls) happens in between — immune to interleaving."""
    instructor_names = []  # parallel to GROUP_KEYS: instructor_names[idx] is homeroom for group idx
    used = {t[0] for t in HERO_TEACHERS.values()}
    for idx in range(len(GROUP_KEYS)):
        if idx in HERO_TEACHERS:
            iname, _email = HERO_TEACHERS[idx]
        else:
            fake.seed_instance(90000 + idx)
            iname = fake.name()
            tries = 0
            while iname in used and tries < 5:
                tries += 1
                fake.seed_instance(90000 + idx * 100 + tries)
                iname = fake.name()
            used.add(iname)
        if not frappe.db.exists("Instructor", {"instructor_name": iname}):
            frappe.get_doc({"doctype": "Instructor", "instructor_name": iname}).insert(ignore_permissions=True)
        instructor_names.append(iname)
    log(f"{len(instructor_names)} instructors")
    return instructor_names


# ---------------------------------------------------------- 4. groups + students + enrollment

def dob_for_grade(grade):
    age = grade + 5  # Class 1 -> ~6yo .. Class 6 -> ~11yo
    return fake.date_of_birth(minimum_age=age, maximum_age=age)


def setup_groups_and_students(instructor_names):
    """Returns {group_idx: {"name":..., "program":..., "section":..., "instructor":..., "students":[student names]}}"""
    roster = {}

    for idx, (g, section) in enumerate(GROUP_KEYS):
        gname = group_name(idx)
        program = f"Class {g}"
        instructor = instructor_names[idx]

        sg = frappe.db.exists("Student Group", gname)
        if not sg:
            sg_doc = frappe.new_doc("Student Group")
            sg_doc.student_group_name = gname
            sg_doc.academic_year = ACADEMIC_YEAR
            sg_doc.academic_term = TERM1_NAME
            sg_doc.group_based_on = "Batch"
            sg_doc.program = program
            sg_doc.batch = section
            sg_doc.max_strength = STUDENTS_PER_GROUP + 5
            sg_doc.append("instructors", {"instructor": instructor})
        else:
            sg_doc = frappe.get_doc("Student Group", gname)

        student_names = []
        for pos in range(STUDENTS_PER_GROUP):
            if idx in HERO_STUDENTS and pos == 0:
                first, last, email = HERO_STUDENTS[idx]
            else:
                # seeded per-(group,position) so identity is stable across runs
                # regardless of any other random/Faker consumption in between
                fake.seed_instance(20000 + idx * 100 + pos)
                first, last = fake.first_name(), fake.last_name()
                email = f"{first.lower()}.{last.lower()}.{idx:02d}{pos:02d}@{SCHOOL_DOMAIN}"

            existing_student = frappe.db.exists("Student", {"student_email_id": email})
            if existing_student:
                student_name = existing_student
            else:
                is_hero = idx in HERO_STUDENTS and pos == 0
                frappe.db.set_single_value("Education Settings", "user_creation_skip", 0 if is_hero else 1)
                s = frappe.new_doc("Student")
                s.first_name = first
                s.last_name = last
                s.student_email_id = email
                s.gender = "Male" if pos % 2 == 0 else "Female"
                s.date_of_birth = dob_for_grade(g)
                s.joining_date = date(YEAR_START.year, 4, 1)
                s.insert(ignore_permissions=True)
                student_name = s.name
                if is_hero:
                    # fix password so the demo login works without relying on the welcome email
                    user = frappe.get_doc("User", email)
                    user.new_password = DEMO_PASSWORD
                    user.send_welcome_email = 0
                    user.save(ignore_permissions=True)
                    # scope this portal user to their own Student record only
                    if not frappe.db.exists("User Permission", {"user": email, "allow": "Student", "for_value": student_name}):
                        frappe.get_doc({
                            "doctype": "User Permission", "user": email,
                            "allow": "Student", "for_value": student_name,
                            "apply_to_all_doctypes": 1,
                        }).insert(ignore_permissions=True)
                    frappe.db.set_single_value("Education Settings", "user_creation_skip", 1)

            student_names.append(student_name)

            # Program Enrollment (submitted — Fee Schedule/Student Group fee generation requires docstatus=1)
            if not frappe.db.exists("Program Enrollment", {"student": student_name, "academic_year": ACADEMIC_YEAR}):
                pe = frappe.new_doc("Program Enrollment")
                pe.student = student_name
                pe.program = program
                pe.academic_year = ACADEMIC_YEAR
                pe.academic_term = TERM1_NAME
                pe.student_batch_name = section
                pe.enrollment_date = date(YEAR_START.year, 4, 5)
                pe.insert(ignore_permissions=True)
                pe.submit()

            # add to the group's own students child table directly (deterministic, no re-query needed)
            if student_name not in {row.student for row in sg_doc.get("students")}:
                sg_doc.append("students", {"student": student_name})

        if not sg:
            sg_doc.insert(ignore_permissions=True)
        else:
            sg_doc.save(ignore_permissions=True)

        roster[idx] = {"name": gname, "program": program, "section": section,
                       "instructor": instructor, "students": student_names}
        log(f"Group {gname}: {len(student_names)} students")

    return roster


# ---------------------------------------------------------- 5. course schedule (one representative week)

def setup_course_schedules(roster, rooms):
    for idx, info in roster.items():
        room = rooms[idx]
        for k, course in enumerate(COURSES):
            weekday_offset = k % 6
            period = PERIODS[k // 6]
            sched_date = WEEK_MONDAY + timedelta(days=weekday_offset)
            existing = frappe.db.exists("Course Schedule", {
                "student_group": info["name"], "course": course, "schedule_date": sched_date,
            })
            if existing:
                continue
            frappe.get_doc({
                "doctype": "Course Schedule",
                "student_group": info["name"], "course": course,
                "instructor": info["instructor"], "room": room,
                "schedule_date": sched_date,
                "from_time": f"{sched_date} {period[0]}",
                "to_time": f"{sched_date} {period[1]}",
            }).insert(ignore_permissions=True)
    log("Course schedules for the representative week")


# ---------------------------------------------------------- 6. attendance (last 4 weeks)

def setup_attendance(roster):
    days = []
    d = TODAY - timedelta(days=27)
    while d <= TODAY:
        if d.weekday() != 6:  # skip Sunday
            days.append(d)
        d += timedelta(days=1)

    created = 0
    for info in roster.values():
        for student in info["students"]:
            for d in days:
                if frappe.db.exists("Student Attendance", {"student": student, "date": d}):
                    continue
                status = random.choices(["Present", "Absent", "Leave"], weights=[90, 7, 3])[0]
                att = frappe.get_doc({
                    "doctype": "Student Attendance", "student": student,
                    "student_group": info["name"], "date": d, "status": status,
                })
                att.insert(ignore_permissions=True)
                att.submit()
                created += 1
    log(f"{created} attendance records over {len(days)} school days")


# ---------------------------------------------------------- 7. fees

def setup_selling_defaults():
    # Sales Invoice requires selling_price_list/price_list_currency/plc_conversion_rate;
    # normally auto-filled by the desk form's client JS from Selling Settings' default,
    # which the setup wizard leaves blank. A one-time site-wide default, safe to set.
    ss = frappe.get_single("Selling Settings")
    if not ss.selling_price_list:
        ss.selling_price_list = "Standard Selling"
        ss.save(ignore_permissions=True)
        log("Selling Settings default price list -> Standard Selling")


def setup_fee_categories():
    # Fee Category.after_insert() auto-creates a matching Item via create_item(),
    # which does not set stock_uom/uom itself (a gap in the app when driven headlessly
    # rather than through the desk form's client-side default). Pre-create the Item
    # with a proper UOM so create_item()'s own "already exists" check just reuses it.
    cats = ["Tuition Fee", "Transport Fee", "Library Fee"]
    for c in cats:
        if not frappe.db.exists("Item", c):
            frappe.get_doc({
                "doctype": "Item", "item_code": c, "item_group": "Fee Component",
                "stock_uom": "Nos", "is_sales_item": 1, "is_service_item": 1, "is_stock_item": 0,
            }).insert(ignore_permissions=True)
        if not frappe.db.exists("Fee Category", c):
            frappe.get_doc({"doctype": "Fee Category", "category_name": c}).insert(ignore_permissions=True)
    return cats


def setup_fee_structures(receivable_account, cost_center):
    structures = {}
    for g_idx, g in enumerate(GRADES):
        program = f"Class {g}"
        name_filter = {"program": program, "academic_year": ACADEMIC_YEAR}
        existing = frappe.db.exists("Fee Structure", name_filter)
        if existing:
            structures[program] = existing
            continue
        tuition = 12000 + 500 * g_idx
        fs = frappe.get_doc({
            "doctype": "Fee Structure", "program": program,
            "academic_year": ACADEMIC_YEAR, "academic_term": TERM1_NAME,
            "company": COMPANY, "receivable_account": receivable_account, "cost_center": cost_center,
            "components": [
                {"fees_category": "Tuition Fee", "amount": tuition},
                {"fees_category": "Transport Fee", "amount": 3000},
                {"fees_category": "Library Fee", "amount": 500},
            ],
        })
        fs.insert(ignore_permissions=True)
        fs.submit()
        structures[program] = fs.name
    log(f"{len(structures)} fee structures")
    return structures


def setup_fee_schedules_and_invoices(structures):
    from education.education.doctype.fee_schedule.fee_schedule import generate_fees, get_fee_structure
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

    schedules_created = []
    for g_idx, g in enumerate(GRADES):
        program = f"Class {g}"
        already_due = g_idx < 3  # Class 1-3: due in the past; Class 4-6: due in the future
        due_date = TODAY - timedelta(days=20) if already_due else TODAY + timedelta(days=10)
        posting_date = due_date - timedelta(days=30)

        existing = frappe.db.exists("Fee Schedule", {"fee_structure": structures[program]})
        if existing:
            schedules_created.append((existing, already_due))
            continue

        group_indices = [i for i, (gr, _s) in enumerate(GROUP_KEYS) if gr == g]
        # Fee Schedule keeps its own copy of the fee components (separate from Fee
        # Structure's own table) — normally filled in by the desk form's "Get Items
        # From" button. get_fee_structure() is that same mapped-doc helper, reused
        # here so the components table is populated exactly as the app expects.
        fsh = get_fee_structure(structures[program])
        fsh.naming_series = "EDU-FSH-.YYYY.-"  # get_mapped_doc bleeds the source's own series otherwise
        fsh.fee_structure = structures[program]
        fsh.academic_year = ACADEMIC_YEAR
        fsh.academic_term = TERM1_NAME
        fsh.program = program
        fsh.company = COMPANY
        fsh.due_date = due_date
        fsh.posting_date = posting_date
        for gi in group_indices:
            fsh.append("student_groups", {
                "student_group": group_name(gi), "total_students": STUDENTS_PER_GROUP,
            })
        fsh.insert(ignore_permissions=True)
        fsh.submit()
        generate_fees(fsh.name)
        schedules_created.append((fsh.name, already_due))
        log(f"Fee Schedule {fsh.name} (due {due_date})")

    # submit generated invoices + apply a realistic paid/partial/overdue mix
    paid, partial, unpaid = 0, 0, 0
    for schedule_name, already_due in schedules_created:
        invoices = frappe.get_all("Sales Invoice", filters={"fee_schedule": schedule_name}, pluck="name")
        for inv_name in invoices:
            inv = frappe.get_doc("Sales Invoice", inv_name)
            if inv.docstatus == 0:
                inv.submit()
                inv.reload()

            if inv.outstanding_amount <= 0:
                continue  # already settled by a prior run

            roll = random.random()
            if already_due:
                if roll < 0.5:
                    amount, tag = None, "full"  # None -> get_payment_entry fills the exact outstanding
                elif roll < 0.8:
                    amount, tag = round(inv.outstanding_amount * random.uniform(0.6, 0.8), 2), "partial"
                else:
                    amount, tag = 0, "none"
            else:
                if roll < 0.3:
                    amount, tag = None, "full"
                else:
                    amount, tag = 0, "none"

            if amount != 0:
                pe = get_payment_entry("Sales Invoice", inv_name, party_amount=amount)
                pe.reference_no = f"DEMO-{inv_name}"
                pe.reference_date = posting_date + timedelta(days=random.randint(1, 18))
                pe.insert(ignore_permissions=True)
                pe.submit()
                if tag == "full":
                    paid += 1
                else:
                    partial += 1
            else:
                unpaid += 1
    log(f"Payments applied — full: {paid}, partial: {partial}, none: {unpaid}")


# ---------------------------------------------------------- 8. mid-term assessment

def setup_midterm_assessment(roster, grading_scale):
    root = "All Assessment Groups"
    exam_group = "Mid-Term Examination"
    if not frappe.db.exists("Assessment Group", exam_group):
        frappe.get_doc({
            "doctype": "Assessment Group", "assessment_group_name": exam_group,
            "parent_assessment_group": root, "is_group": 0,
        }).insert(ignore_permissions=True)

    for c in EXAM_COURSES:
        if not frappe.db.exists("Assessment Criteria", c):
            frappe.get_doc({"doctype": "Assessment Criteria", "assessment_criteria": c}).insert(ignore_permissions=True)

    plans_created, results_created = 0, 0
    for idx, info in roster.items():
        program = info["program"]
        examiner = info["instructor"]
        for e_idx, course in enumerate(EXAM_COURSES):
            sched_date = ASSESS_MONDAY + timedelta(days=e_idx)
            existing_plan = frappe.db.exists("Assessment Plan", {
                "student_group": info["name"], "course": course, "assessment_group": exam_group,
            })
            if existing_plan:
                plan_name = existing_plan
            else:
                plan = frappe.get_doc({
                    "doctype": "Assessment Plan",
                    "student_group": info["name"], "course": course, "program": program,
                    "academic_year": ACADEMIC_YEAR, "academic_term": TERM1_NAME,
                    "assessment_group": exam_group, "grading_scale": grading_scale,
                    "schedule_date": sched_date,
                    "from_time": f"{sched_date} 09:00:00", "to_time": f"{sched_date} 10:30:00",
                    "examiner": examiner, "supervisor": examiner,
                    "maximum_assessment_score": 100,
                    "assessment_criteria": [{"assessment_criteria": course, "maximum_score": 100}],
                })
                plan.insert(ignore_permissions=True)
                plan.submit()
                plan_name = plan.name
                plans_created += 1

            for student in info["students"]:
                if frappe.db.exists("Assessment Result", {"assessment_plan": plan_name, "student": student}):
                    continue
                score = max(35, min(100, round(random.gauss(72, 12))))
                res = frappe.get_doc({
                    "doctype": "Assessment Result", "assessment_plan": plan_name, "student": student,
                    "student_name": frappe.db.get_value("Student", student, "student_name"),
                    "program": program, "student_group": info["name"],
                    "details": [{"assessment_criteria": course, "maximum_score": 100, "score": score}],
                    "total_score": score, "maximum_score": 100,
                })
                res.insert(ignore_permissions=True)
                res.submit()
                results_created += 1

    log(f"Mid-term: {plans_created} assessment plans, {results_created} results")


# ---------------------------------------------------------- 9. permission fixes for Instructor role

def ensure_custom_docperm(doctype, role, **flags):
    # IMPORTANT: the moment a doctype has ANY Custom DocPerm row, frappe treats
    # Custom DocPerm as the *complete* permission set for that doctype and stops
    # consulting its shipped standard permissions entirely. setup_custom_perms()
    # copies the standard rows over first so adding one new rule doesn't silently
    # wipe out every other role's existing access (e.g. Academics User, Student).
    frappe.permissions.setup_custom_perms(doctype)
    if frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0}):
        return
    doc = {"doctype": "Custom DocPerm", "parent": doctype, "parenttype": "DocType",
           "parentfield": "permissions", "role": role, "permlevel": 0, "read": 1}
    doc.update(flags)
    frappe.get_doc(doc).insert(ignore_permissions=True)
    log(f"Custom DocPerm: {role} on {doctype} -> {flags}")


def setup_instructor_permission_fixes(roster):
    ensure_custom_docperm("Course Schedule", "Instructor", read=1)
    ensure_custom_docperm("Student Attendance", "Instructor", read=1, create=1, write=1, submit=1)
    ensure_custom_docperm("Assessment Plan", "Instructor", read=1)
    ensure_custom_docperm("Assessment Result", "Instructor", read=1, create=1, write=1, submit=1)

    # scope each hero teacher to just their own group (and their own Instructor record)
    for idx, (iname, email) in HERO_TEACHERS.items():
        gname = roster[idx]["name"]
        if not frappe.db.exists("User Permission", {"user": email, "allow": "Student Group", "for_value": gname}):
            frappe.get_doc({
                "doctype": "User Permission", "user": email,
                "allow": "Student Group", "for_value": gname, "apply_to_all_doctypes": 1,
            }).insert(ignore_permissions=True)
        if not frappe.db.exists("User Permission", {"user": email, "allow": "Instructor", "for_value": iname}):
            frappe.get_doc({
                "doctype": "User Permission", "user": email,
                "allow": "Instructor", "for_value": iname, "apply_to_all_doctypes": 1,
            }).insert(ignore_permissions=True)
    log("Instructor permission fixes + hero-teacher scoping")


# ---------------------------------------------------------- 10. role profiles + staff users

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


def setup_role_profiles_and_users():
    ensure_role_profile("Principal Admin", ["System Manager", "Education Manager", "Academics User", "Accounts Manager"])
    ensure_role_profile("Front Office Staff", ["Academics User"])
    ensure_role_profile("Teacher", ["Instructor"])
    ensure_role_profile("Fee Clerk", ["Accounts User"])

    ensure_user("principal@" + SCHOOL_DOMAIN, "Anjali", "Verma", "Principal Admin")
    ensure_user("registrar@" + SCHOOL_DOMAIN, "Meera", "Iyer", "Front Office Staff")
    ensure_user("suresh.pillai@" + SCHOOL_DOMAIN, "Suresh", "Pillai", "Fee Clerk")
    for idx, (iname, email) in HERO_TEACHERS.items():
        first, last = iname.split(" ", 1)
        ensure_user(email, first, last, "Teacher")
    log("Role Profiles + staff users")


# ---------------------------------------------------------- 11. dashboards / workspace

def ensure_number_card(label, document_type, filters, function="Count", based_on=None, is_public=1):
    if frappe.db.exists("Number Card", label):
        return label
    doc = {
        "doctype": "Number Card", "label": label, "document_type": document_type,
        "function": function, "filters_json": frappe.as_json(filters), "is_public": is_public,
        "show_percentage_stats": 0,
    }
    if based_on:
        doc["aggregate_function_based_on"] = based_on
    frappe.get_doc(doc).insert(ignore_permissions=True)
    return label


def ensure_chart(name, chart_type, document_type, filters, **kw):
    if frappe.db.exists("Dashboard Chart", name):
        return name
    doc = {
        "doctype": "Dashboard Chart", "chart_name": name, "chart_type": chart_type,
        "document_type": document_type, "filters_json": frappe.as_json(filters),
        "is_public": 1, "timeseries": 0,
    }
    doc.update(kw)
    frappe.get_doc(doc).insert(ignore_permissions=True)
    return name


def setup_dashboards_and_workspace():
    cards = []
    cards.append(ensure_number_card("Total Students", "Student", [["Student", "enabled", "=", 1]]))
    cards.append(ensure_number_card("Total Instructors", "Instructor", [["Instructor", "status", "=", "Active"]]))
    cards.append(ensure_number_card("Active Programs", "Program", []))
    cards.append(ensure_number_card(
        "Fee Invoiced", "Sales Invoice",
        [["Sales Invoice", "docstatus", "=", 1], ["Sales Invoice", "fee_schedule", "is", "set"]],
        function="Sum", based_on="grand_total",
    ))
    cards.append(ensure_number_card(
        "Fee Outstanding", "Sales Invoice",
        [["Sales Invoice", "docstatus", "=", 1], ["Sales Invoice", "fee_schedule", "is", "set"]],
        function="Sum", based_on="outstanding_amount",
    ))
    cards.append(ensure_number_card(
        "Fee Overdue", "Sales Invoice",
        [["Sales Invoice", "docstatus", "=", 1], ["Sales Invoice", "fee_schedule", "is", "set"],
         ["Sales Invoice", "due_date", "<", frappe.utils.nowdate()]],
        function="Sum", based_on="outstanding_amount",
    ))

    charts = []
    charts.append(ensure_chart(
        "Students by Program", "Group By", "Program Enrollment",
        [["Program Enrollment", "docstatus", "=", 1]],
        group_by_based_on="program", group_by_type="Count", number_of_groups=6,
    ))
    charts.append(ensure_chart(
        "Fee Collection Trend", "Sum", "Payment Entry",
        [["Payment Entry", "payment_type", "=", "Receive"], ["Payment Entry", "party_type", "=", "Customer"]],
        based_on="posting_date", value_based_on="paid_amount", timeseries=1,
        time_interval="Daily", timespan="Last Month",
    ))
    charts.append(ensure_chart(
        "Attendance Trend", "Group By", "Student Attendance", [],
        based_on="date", group_by_based_on="status", timeseries=1,
        time_interval="Daily", timespan="Last Month",
    ))
    charts.append(ensure_chart(
        "Fee Status Split", "Group By", "Sales Invoice",
        [["Sales Invoice", "docstatus", "=", 1], ["Sales Invoice", "fee_schedule", "is", "set"]],
        group_by_based_on="status", group_by_type="Count",
    ))

    # attach to the existing "Education" workspace
    ws = frappe.get_doc("Workspace", "Education")
    if not ws.type:
        ws.type = "Workspace"  # shipped fixture leaves this NULL; schema requires it on save
    existing_cards = {c.number_card_name for c in ws.get("number_cards")}
    existing_charts = {c.chart_name for c in ws.get("charts")}
    content = frappe.parse_json(ws.content) if ws.content else []
    content.append({"id": frappe.generate_hash(length=10), "type": "header",
                     "data": {"text": "<span class=\"h4\"><b>School Overview</b></span>", "col": 12}})
    for c in cards:
        if c not in existing_cards:
            ws.append("number_cards", {"number_card_name": c, "label": c})
            content.append({"id": frappe.generate_hash(length=10), "type": "number_card",
                             "data": {"number_card_name": c, "col": 4}})
    for c in charts:
        if c not in existing_charts:
            ws.append("charts", {"chart_name": c, "label": c})
            content.append({"id": frappe.generate_hash(length=10), "type": "chart",
                             "data": {"chart_name": c, "col": 6}})
    ws.content = frappe.as_json(content)
    ws.save(ignore_permissions=True)

    # role-scoped landing workspace for teachers
    if not frappe.db.exists("Workspace", "Teacher Portal"):
        tw = frappe.new_doc("Workspace")
        tw.label = "Teacher Portal"
        tw.title = "Teacher Portal"
        tw.module = "Education"
        tw.public = 1
        tw.icon = "education"
        tw.append("roles", {"role": "Instructor"})
        for c in ["Total Students", "Total Instructors"]:
            tw.append("number_cards", {"number_card_name": c, "label": c})
        tw.append("charts", {"chart_name": "Attendance Trend", "label": "Attendance Trend"})
        tw.append("shortcuts", {"type": "DocType", "link_to": "Course Schedule", "label": "My Timetable", "color": "Blue"})
        tw.append("shortcuts", {"type": "DocType", "link_to": "Student Attendance", "label": "Mark Attendance", "color": "Green"})
        tw.append("shortcuts", {"type": "DocType", "link_to": "Assessment Result", "label": "Enter Grades", "color": "Orange"})
        content = [
            {"id": frappe.generate_hash(length=10), "type": "header",
             "data": {"text": "<span class=\"h4\"><b>Your Shortcuts</b></span>", "col": 12}},
            {"id": frappe.generate_hash(length=10), "type": "shortcut", "data": {"shortcut_name": "My Timetable", "col": 4}},
            {"id": frappe.generate_hash(length=10), "type": "shortcut", "data": {"shortcut_name": "Mark Attendance", "col": 4}},
            {"id": frappe.generate_hash(length=10), "type": "shortcut", "data": {"shortcut_name": "Enter Grades", "col": 4}},
            {"id": frappe.generate_hash(length=10), "type": "chart", "data": {"chart_name": "Attendance Trend", "col": 12}},
        ]
        tw.content = frappe.as_json(content)
        tw.insert(ignore_permissions=True)
    log("Dashboards + workspaces")


# ---------------------------------------------------------- run all

def run_all():
    setup_company_and_fiscal_year()
    fix_student_role_desk_access()
    setup_academic_calendar()
    setup_holiday_list()
    grading_scale = setup_grading_scale()
    rooms = setup_rooms()
    setup_batches()
    setup_programs()
    setup_courses()
    instructor_names = setup_instructors()
    roster = setup_groups_and_students(instructor_names)
    frappe.db.commit()

    setup_course_schedules(roster, rooms)
    frappe.db.commit()

    setup_attendance(roster)
    frappe.db.commit()

    setup_selling_defaults()
    setup_fee_categories()
    receivable_account, cost_center = frappe.get_cached_value(
        "Company", COMPANY, ["default_receivable_account", "cost_center"]
    )
    structures = setup_fee_structures(receivable_account, cost_center)
    setup_fee_schedules_and_invoices(structures)
    frappe.db.commit()

    setup_midterm_assessment(roster, grading_scale)
    frappe.db.commit()

    setup_role_profiles_and_users()
    setup_instructor_permission_fixes(roster)
    setup_dashboards_and_workspace()
    frappe.db.commit()

    frappe.clear_cache()
    log("Done.")


if __name__ == "__main__":
    run_all()
    frappe.db.commit()
