from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)

app.secret_key = "internshipbridge_secret_key"

DATABASE = "internshipbridge.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# DATABASE SETUP + MIGRATION
# =========================================================

def init_database():

    conn = get_db_connection()

    # Create table if it does not exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            college TEXT NOT NULL,
            department TEXT NOT NULL,
            year TEXT NOT NULL,
            internship TEXT DEFAULT '',
            reason TEXT DEFAULT '',
            status TEXT DEFAULT 'Pending'
        )
    """)

    conn.commit()

    # -----------------------------------------------------
    # CHECK EXISTING COLUMNS
    # -----------------------------------------------------

    columns = conn.execute("""
        PRAGMA table_info(applications)
    """).fetchall()

    column_names = [column["name"] for column in columns]

    # Add internship column if missing
    if "internship" not in column_names:

        conn.execute("""
            ALTER TABLE applications
            ADD COLUMN internship TEXT DEFAULT ''
        """)

    # Add reason column if missing
    if "reason" not in column_names:

        conn.execute("""
            ALTER TABLE applications
            ADD COLUMN reason TEXT DEFAULT ''
        """)

    # Add status column if missing
    if "status" not in column_names:

        conn.execute("""
            ALTER TABLE applications
            ADD COLUMN status TEXT DEFAULT 'Pending'
        """)

    conn.commit()

    conn.close()


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def index():

    return render_template("index.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    # Open login page
    if request.method == "GET":

        return render_template("login.html")

    # Get form values
    email = request.form.get("email", "").strip()

    password = request.form.get("password", "").strip()


    # -----------------------------------------------------
    # ADMIN LOGIN
    # -----------------------------------------------------

    if email == "admin@gmail.com" and password == "admin123":

        session.clear()

        session["user"] = "admin"

        session["role"] = "admin"

        return redirect(url_for("admin"))


    # -----------------------------------------------------
    # STUDENT LOGIN
    # -----------------------------------------------------

    if email and password:

        session.clear()

        session["user"] = email

        session["role"] = "student"

        return redirect(url_for("student_dashboard"))


    # Invalid login
    flash("Please enter a valid email and password.")

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("index"))


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@app.route("/student-dashboard")
def student_dashboard():

    if session.get("role") != "student":
        return redirect(url_for("login"))

    email = session.get("user")

    conn = get_db_connection()

    applications = conn.execute("""
        SELECT *
        FROM applications
        WHERE email = ?
        ORDER BY id DESC
    """, (email,)).fetchall()

    conn.close()

    return render_template(
        "student_dashboard.html",
        applications=applications
    )

# =========================================================
# INTERNSHIPS PAGE
# =========================================================

@app.route("/internships")
def internships():

    return render_template("internships.html")


# =========================================================
# APPLY FOR INTERNSHIP
# =========================================================

@app.route("/apply", methods=["GET", "POST"])
def apply():

    # Student must login before applying
    if "user" not in session:
        return redirect(url_for("login"))

    if session.get("role") == "admin":
        return redirect(url_for("admin"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        college = request.form.get("college", "").strip()
        department = request.form.get("department", "").strip()
        year = request.form.get("year", "").strip()

        internship = request.form.get(
            "internship",
            request.form.get("title", "")
        ).strip()

        reason = request.form.get("reason", "").strip()

        if not name or not email or not college or not department or not year:

            flash("Please fill all required fields.")

            return render_template("apply.html")

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO applications
            (name, email, college, department, year, internship, reason, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            email,
            college,
            department,
            year,
            internship,
            reason,
            "Pending"
        ))

        conn.commit()
        conn.close()

        flash("Application submitted successfully!")

        return redirect(url_for("my_applications"))

    return render_template("apply.html")

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not name:

        flash("Please enter your name.")

        return render_template("apply.html")


    if not email:

        flash("Please enter your email.")

        return render_template("apply.html")


    if not college:

        flash("Please enter your college.")

        return render_template("apply.html")


    if not department:

        flash("Please enter your department.")

        return render_template("apply.html")


    if not year:

        flash("Please select your year.")

        return render_template("apply.html")


    # -----------------------------------------------------
    # INSERT APPLICATION
    # -----------------------------------------------------

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO applications
        (
            name,
            email,
            college,
            department,
            year,
            internship,
            reason,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        email,
        college,
        department,
        year,
        internship,
        reason,
        "Pending"
    ))

    conn.commit()

    conn.close()


    flash("Application submitted successfully!")

    return redirect(url_for("my_applications"))

# =========================================================
# MY APPLICATIONS
# =========================================================

@app.route("/my-applications")
def my_applications():

    # Student must be logged in
    if session.get("role") != "student":
        return redirect(url_for("login"))

    # Get logged-in student's email
    email = session.get("user")

    conn = get_db_connection()

    # Show ONLY this student's applications
    applications = conn.execute("""
        SELECT *
        FROM applications
        WHERE email = ?
        ORDER BY id DESC
    """, (email,)).fetchall()

    conn.close()

    return render_template(
        "my_applications.html",
        applications=applications
    )

# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin():

    # Only admin can access
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()

    applications = conn.execute("""
        SELECT *
        FROM applications
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        applications=applications
    )

# =========================================================
# UPDATE APPLICATION STATUS
# =========================================================

@app.route("/update-status/<int:application_id>/<status>", methods=["POST"])
def update_status(application_id, status):

    # Only admin can change application status
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    # Allow only Approved or Rejected
    if status not in ["Approved", "Rejected"]:
        return "Invalid status", 400

    conn = get_db_connection()

    conn.execute("""
        UPDATE applications
        SET status = ?
        WHERE id = ?
    """, (status, application_id))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# =========================================================
# DELETE APPLICATION
# =========================================================

@app.route(
    "/delete-application/<int:application_id>",
    methods=["POST"]
)
def delete_application(application_id):

    # Admin only
    if session.get("role") != "admin":

        return redirect(url_for("login"))


    conn = get_db_connection()

    conn.execute("""
        DELETE FROM applications
        WHERE id = ?
    """, (application_id,))

    conn.commit()

    conn.close()


    return redirect(url_for("admin"))


# =========================================================
# TEST ROUTE
# =========================================================

@app.route("/test")
def test():

    return "TEST ROUTE IS WORKING"


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    # Create / update database
    init_database()


    print("----------------------------------------")
    print(" InternshipBridge")
    print(" Flask Application Started")
    print("----------------------------------------")
    print(" Home:")
    print(" http://127.0.0.1:5000/")
    print("----------------------------------------")
    print(" Login:")
    print(" http://127.0.0.1:5000/login")
    print("----------------------------------------")
    print(" Student Dashboard:")
    print(" http://127.0.0.1:5000/student-dashboard")
    print("----------------------------------------")
    print(" Admin:")
    print(" http://127.0.0.1:5000/admin")
    print("----------------------------------------")


    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )