from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "yanas_gallery_secret"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ================= DATABASE INIT =================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # PRODUCTS TABLE
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            stock INTEGER NOT NULL,
            image TEXT NOT NULL
        )
    """)

    # ADMIN TABLE
    c.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # CONTACT TABLE
    c.execute("""
        CREATE TABLE IF NOT EXISTS contact (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            whatsapp TEXT,
            instagram TEXT,
            email TEXT
        )
    """)

    # DEFAULT ADMIN (IF NOT EXISTS)
    c.execute("SELECT * FROM admin")
    if not c.fetchone():
        c.execute("INSERT INTO admin (username, password) VALUES (?, ?)",
                  ("admin", "admin123"))

    # DEFAULT CONTACT (IF NOT EXISTS)
    c.execute("SELECT * FROM contact")
    if not c.fetchone():
        c.execute("INSERT INTO contact (whatsapp, instagram, email) VALUES (?, ?, ?)",
                  ("919876543210", "https://instagram.com", "example@gmail.com"))

    conn.commit()
    conn.close()


init_db()


# ================= HOME (PUBLIC GALLERY) =================
@app.route("/")
def home():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT * FROM products ORDER BY id DESC")
    products = c.fetchall()

    c.execute("SELECT * FROM contact LIMIT 1")
    contact = c.fetchone()

    conn.close()

    return render_template("gallery.html", products=products, contact=contact)


# ================= ADMIN LOGIN =================
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM admin WHERE username=? AND password=?",
                  (username, password))
        admin = c.fetchone()
        conn.close()

        if admin:
            session["admin"] = True
            return redirect("/dashboard")

    return render_template("login.html")


# ================= DASHBOARD =================
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "admin" not in session:
        return redirect("/admin")

    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        stock = request.form["stock"]
        image = request.files["image"]

        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "INSERT INTO products (name, price, stock, image) VALUES (?, ?, ?, ?)",
                (name, price, stock, filename)
            )
            conn.commit()
            conn.close()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT * FROM products ORDER BY id DESC")
    products = c.fetchall()

    c.execute("SELECT * FROM contact LIMIT 1")
    contact = c.fetchone()

    conn.close()

    return render_template("dashboard.html", products=products, contact=contact)


# ================= CHANGE ADMIN CREDENTIALS =================
@app.route("/change_credentials", methods=["POST"])
def change_credentials():
    if "admin" not in session:
        return redirect("/admin")

    new_username = request.form["new_username"]
    new_password = request.form["new_password"]

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE admin SET username=?, password=? WHERE id=1",
              (new_username, new_password))
    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ================= UPDATE CONTACT DETAILS =================
@app.route("/update_contact", methods=["POST"])
def update_contact():
    if "admin" not in session:
        return redirect("/admin")

    whatsapp = request.form["whatsapp"]
    instagram = request.form["instagram"]
    email = request.form["email"]

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE contact SET whatsapp=?, instagram=?, email=? WHERE id=1",
              (whatsapp, instagram, email))
    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ================= DELETE PRODUCT =================
@app.route("/delete/<int:product_id>")
def delete(product_id):
    if "admin" not in session:
        return redirect("/admin")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)