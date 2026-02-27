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


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER,
        stock INTEGER,
        image TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS contact (
        id INTEGER PRIMARY KEY,
        phone1 TEXT,
        phone2 TEXT,
        instagram TEXT,
        email TEXT
    )
    """)

    c.execute("SELECT * FROM admin")
    if not c.fetchone():
        c.execute(
            "INSERT INTO admin (username,password) VALUES (?,?)",
            ("admin", "admin123"),
        )

    c.execute("SELECT * FROM contact WHERE id=1")
    if not c.fetchone():
        c.execute(
            "INSERT INTO contact VALUES (1,?,?,?,?)",
            ("9876543210", "9123456780", "https://instagram.com", "example@gmail.com"),
        )

    conn.commit()
    conn.close()


init_db()


# HOME → STORY
@app.route("/")
def home():
    return render_template("story.html")


# GALLERY PAGE
@app.route("/gallery")
def gallery():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT * FROM products ORDER BY id DESC")
    products = c.fetchall()

    c.execute("SELECT * FROM contact WHERE id=1")
    contact = c.fetchone()

    conn.close()

    return render_template("gallery.html", products=products, contact=contact)


# ADMIN LOGIN
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute(
            "SELECT * FROM admin WHERE username=? AND password=?",
            (username, password),
        )
        admin = c.fetchone()

        conn.close()

        if admin:
            session["admin"] = True
            return redirect("/dashboard")

    return render_template("login.html")


# DASHBOARD
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "admin" not in session:
        return redirect("/admin")

    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        stock = request.form["stock"]
        image = request.files["image"]

        filename = ""

        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute(
            "INSERT INTO products (name,price,stock,image) VALUES (?,?,?,?)",
            (name, price, stock, filename),
        )

        conn.commit()
        conn.close()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT * FROM products ORDER BY id DESC")
    products = c.fetchall()

    c.execute("SELECT * FROM contact WHERE id=1")
    contact = c.fetchone()

    conn.close()

    return render_template("dashboard.html", products=products, contact=contact)


# LOGOUT
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")


if __name__ == "__main__":
    app.run()

