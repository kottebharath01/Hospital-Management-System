"""Beginner-friendly Hospital Management System built with Flask and SQLite."""

import os
import sqlite3
from datetime import date, datetime

from flask import Flask, flash, g, redirect, render_template, request, url_for


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-in-production")
app.config["DATABASE"] = os.path.join(app.root_path, "hospital.db")


def get_db():
    """Open one database connection for the current web request."""
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    database = g.pop("db", None)
    if database is not None:
        database.close()


def init_db():
    """Create tables and insert starter data the first time the app runs."""
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL CHECK(age >= 0),
            gender TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT,
            blood_group TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            room_number TEXT,
            available_days TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            reason TEXT,
            status TEXT NOT NULL DEFAULT 'Scheduled',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE RESTRICT,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount >= 0),
            bill_date TEXT NOT NULL,
            payment_status TEXT NOT NULL DEFAULT 'Unpaid',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE RESTRICT
        );
        """
    )

    if db.execute("SELECT COUNT(*) FROM patients").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO patients (name, age, gender, phone, address, blood_group) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("Aarav Sharma", 34, "Male", "9876543210", "MG Road, Pune", "O+"),
                ("Meera Patel", 28, "Female", "9876501234", "Navrangpura, Ahmedabad", "B+"),
            ],
        )
        db.executemany(
            "INSERT INTO doctors (name, specialization, phone, email, room_number, available_days) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("Dr. Ananya Rao", "Cardiology", "9820011122", "ananya@example.com", "201", "Mon, Wed, Fri"),
                ("Dr. Rohan Gupta", "General Medicine", "9820033344", "rohan@example.com", "105", "Mon - Sat"),
            ],
        )
        db.execute(
            "INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason, status) VALUES (?, ?, ?, ?, ?, ?)",
            (1, 2, date.today().isoformat(), "10:30", "General check-up", "Scheduled"),
        )
        db.execute(
            "INSERT INTO bills (patient_id, description, amount, bill_date, payment_status) VALUES (?, ?, ?, ?, ?)",
            (1, "Consultation fee", 600, date.today().isoformat(), "Unpaid"),
        )
    db.commit()


def form_value(name):
    """Read and trim a form value."""
    return request.form.get(name, "").strip()


@app.route("/")
def dashboard():
    db = get_db()
    stats = {
        "patients": db.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
        "doctors": db.execute("SELECT COUNT(*) FROM doctors").fetchone()[0],
        "appointments": db.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date = ?", (date.today().isoformat(),)).fetchone()[0],
        "unpaid": db.execute("SELECT COALESCE(SUM(amount), 0) FROM bills WHERE payment_status = 'Unpaid'").fetchone()[0],
    }
    appointments = db.execute(
        """SELECT appointments.*, patients.name AS patient_name, doctors.name AS doctor_name
           FROM appointments JOIN patients ON patients.id = appointments.patient_id
           JOIN doctors ON doctors.id = appointments.doctor_id
           ORDER BY appointment_date ASC, appointment_time ASC LIMIT 6"""
    ).fetchall()
    return render_template("dashboard.html", stats=stats, appointments=appointments, today=date.today().isoformat())


@app.route("/patients")
def patients():
    search = request.args.get("search", "").strip()
    rows = get_db().execute(
        "SELECT * FROM patients WHERE name LIKE ? OR phone LIKE ? ORDER BY id DESC",
        (f"%{search}%", f"%{search}%"),
    ).fetchall()
    return render_template("patients/list.html", patients=rows, search=search)


@app.route("/patients/add", methods=["GET", "POST"])
def add_patient():
    if request.method == "POST":
        try:
            age = int(form_value("age"))
            if age < 0:
                raise ValueError
            db = get_db()
            db.execute(
                "INSERT INTO patients (name, age, gender, phone, address, blood_group) VALUES (?, ?, ?, ?, ?, ?)",
                (form_value("name"), age, form_value("gender"), form_value("phone"), form_value("address"), form_value("blood_group")),
            )
            db.commit()
            flash("Patient added successfully.", "success")
            return redirect(url_for("patients"))
        except (ValueError, sqlite3.IntegrityError):
            flash("Please enter valid patient details.", "danger")
    return render_template("patients/form.html", patient=None)


@app.route("/patients/<int:patient_id>/edit", methods=["GET", "POST"])
def edit_patient(patient_id):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    if patient is None:
        flash("Patient not found.", "danger")
        return redirect(url_for("patients"))
    if request.method == "POST":
        try:
            age = int(form_value("age"))
            db.execute(
                "UPDATE patients SET name=?, age=?, gender=?, phone=?, address=?, blood_group=? WHERE id=?",
                (form_value("name"), age, form_value("gender"), form_value("phone"), form_value("address"), form_value("blood_group"), patient_id),
            )
            db.commit()
            flash("Patient updated successfully.", "success")
            return redirect(url_for("patients"))
        except (ValueError, sqlite3.IntegrityError):
            flash("Please enter valid patient details.", "danger")
    return render_template("patients/form.html", patient=patient)


@app.post("/patients/<int:patient_id>/delete")
def delete_patient(patient_id):
    try:
        db = get_db()
        db.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        db.commit()
        flash("Patient deleted.", "success")
    except sqlite3.IntegrityError:
        flash("This patient has appointments or bills and cannot be deleted.", "danger")
    return redirect(url_for("patients"))


@app.route("/doctors")
def doctors():
    rows = get_db().execute("SELECT * FROM doctors ORDER BY id DESC").fetchall()
    return render_template("doctors/list.html", doctors=rows)


@app.route("/doctors/add", methods=["GET", "POST"])
def add_doctor():
    if request.method == "POST":
        try:
            db = get_db()
            db.execute(
                "INSERT INTO doctors (name, specialization, phone, email, room_number, available_days) VALUES (?, ?, ?, ?, ?, ?)",
                tuple(form_value(key) for key in ("name", "specialization", "phone", "email", "room_number", "available_days")),
            )
            db.commit()
            flash("Doctor added successfully.", "success")
            return redirect(url_for("doctors"))
        except sqlite3.IntegrityError:
            flash("Please complete the required fields.", "danger")
    return render_template("doctors/form.html", doctor=None)


@app.route("/doctors/<int:doctor_id>/edit", methods=["GET", "POST"])
def edit_doctor(doctor_id):
    db = get_db()
    doctor = db.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,)).fetchone()
    if doctor is None:
        flash("Doctor not found.", "danger")
        return redirect(url_for("doctors"))
    if request.method == "POST":
        db.execute(
            "UPDATE doctors SET name=?, specialization=?, phone=?, email=?, room_number=?, available_days=? WHERE id=?",
            (*tuple(form_value(key) for key in ("name", "specialization", "phone", "email", "room_number", "available_days")), doctor_id),
        )
        db.commit()
        flash("Doctor updated successfully.", "success")
        return redirect(url_for("doctors"))
    return render_template("doctors/form.html", doctor=doctor)


@app.post("/doctors/<int:doctor_id>/delete")
def delete_doctor(doctor_id):
    try:
        db = get_db()
        db.execute("DELETE FROM doctors WHERE id = ?", (doctor_id,))
        db.commit()
        flash("Doctor deleted.", "success")
    except sqlite3.IntegrityError:
        flash("This doctor has appointments and cannot be deleted.", "danger")
    return redirect(url_for("doctors"))


def appointment_options():
    db = get_db()
    return (
        db.execute("SELECT id, name FROM patients ORDER BY name").fetchall(),
        db.execute("SELECT id, name, specialization FROM doctors ORDER BY name").fetchall(),
    )


@app.route("/appointments")
def appointments():
    rows = get_db().execute(
        """SELECT appointments.*, patients.name AS patient_name, doctors.name AS doctor_name,
                  doctors.specialization FROM appointments
           JOIN patients ON patients.id = appointments.patient_id
           JOIN doctors ON doctors.id = appointments.doctor_id
           ORDER BY appointment_date DESC, appointment_time DESC"""
    ).fetchall()
    return render_template("appointments/list.html", appointments=rows)


@app.route("/appointments/add", methods=["GET", "POST"])
def add_appointment():
    if request.method == "POST":
        try:
            db = get_db()
            db.execute(
                "INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason, status) VALUES (?, ?, ?, ?, ?, ?)",
                (int(form_value("patient_id")), int(form_value("doctor_id")), form_value("appointment_date"), form_value("appointment_time"), form_value("reason"), form_value("status")),
            )
            db.commit()
            flash("Appointment booked successfully.", "success")
            return redirect(url_for("appointments"))
        except (ValueError, sqlite3.IntegrityError):
            flash("Please complete all appointment details.", "danger")
    patient_rows, doctor_rows = appointment_options()
    return render_template("appointments/form.html", appointment=None, patients=patient_rows, doctors=doctor_rows, today=date.today().isoformat())


@app.route("/appointments/<int:appointment_id>/edit", methods=["GET", "POST"])
def edit_appointment(appointment_id):
    db = get_db()
    appointment = db.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,)).fetchone()
    if appointment is None:
        flash("Appointment not found.", "danger")
        return redirect(url_for("appointments"))
    if request.method == "POST":
        db.execute(
            "UPDATE appointments SET patient_id=?, doctor_id=?, appointment_date=?, appointment_time=?, reason=?, status=? WHERE id=?",
            (int(form_value("patient_id")), int(form_value("doctor_id")), form_value("appointment_date"), form_value("appointment_time"), form_value("reason"), form_value("status"), appointment_id),
        )
        db.commit()
        flash("Appointment updated successfully.", "success")
        return redirect(url_for("appointments"))
    patient_rows, doctor_rows = appointment_options()
    return render_template("appointments/form.html", appointment=appointment, patients=patient_rows, doctors=doctor_rows, today=date.today().isoformat())


@app.post("/appointments/<int:appointment_id>/delete")
def delete_appointment(appointment_id):
    db = get_db()
    db.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
    db.commit()
    flash("Appointment deleted.", "success")
    return redirect(url_for("appointments"))


@app.route("/bills")
def bills():
    rows = get_db().execute(
        """SELECT bills.*, patients.name AS patient_name FROM bills
           JOIN patients ON patients.id = bills.patient_id ORDER BY bill_date DESC, bills.id DESC"""
    ).fetchall()
    total = sum(row["amount"] for row in rows)
    return render_template("bills/list.html", bills=rows, total=total)


@app.route("/bills/add", methods=["GET", "POST"])
def add_bill():
    if request.method == "POST":
        try:
            db = get_db()
            db.execute(
                "INSERT INTO bills (patient_id, description, amount, bill_date, payment_status) VALUES (?, ?, ?, ?, ?)",
                (int(form_value("patient_id")), form_value("description"), float(form_value("amount")), form_value("bill_date"), form_value("payment_status")),
            )
            db.commit()
            flash("Bill created successfully.", "success")
            return redirect(url_for("bills"))
        except (ValueError, sqlite3.IntegrityError):
            flash("Please enter valid bill details.", "danger")
    patient_rows = get_db().execute("SELECT id, name FROM patients ORDER BY name").fetchall()
    return render_template("bills/form.html", bill=None, patients=patient_rows, today=date.today().isoformat())


@app.route("/bills/<int:bill_id>/edit", methods=["GET", "POST"])
def edit_bill(bill_id):
    db = get_db()
    bill = db.execute("SELECT * FROM bills WHERE id = ?", (bill_id,)).fetchone()
    if bill is None:
        flash("Bill not found.", "danger")
        return redirect(url_for("bills"))
    if request.method == "POST":
        db.execute(
            "UPDATE bills SET patient_id=?, description=?, amount=?, bill_date=?, payment_status=? WHERE id=?",
            (int(form_value("patient_id")), form_value("description"), float(form_value("amount")), form_value("bill_date"), form_value("payment_status"), bill_id),
        )
        db.commit()
        flash("Bill updated successfully.", "success")
        return redirect(url_for("bills"))
    patient_rows = db.execute("SELECT id, name FROM patients ORDER BY name").fetchall()
    return render_template("bills/form.html", bill=bill, patients=patient_rows, today=date.today().isoformat())


@app.post("/bills/<int:bill_id>/delete")
def delete_bill(bill_id):
    db = get_db()
    db.execute("DELETE FROM bills WHERE id = ?", (bill_id,))
    db.commit()
    flash("Bill deleted.", "success")
    return redirect(url_for("bills"))


@app.template_filter("money")
def money(value):
    return f"₹{float(value):,.2f}"


@app.context_processor
def inject_year():
    return {"current_year": datetime.now().year}


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=True)
