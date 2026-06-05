import os
import sqlite3

from flask import Flask, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

# ── App Config ─────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "laporaman_ctf_secret_2024")

DATABASE_URL = os.environ.get("DATABASE_URL")   # Set di Vercel env vars
USE_PG       = bool(DATABASE_URL)               # True = Supabase, False = SQLite
PH           = "%s" if USE_PG else "?"          # Parameterized query placeholder

if USE_PG:
    import psycopg2
    import psycopg2.extras

# ── Database Helpers ───────────────────────────────────────────
def get_db():
    """Ambil koneksi database (SQLite reuse per-request, PostgreSQL baru per-call)."""
    if USE_PG:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        return conn
    else:
        db = getattr(g, "_database", None)
        if db is None:
            db = g._database = sqlite3.connect("laporaman.db")
            db.row_factory = sqlite3.Row
        return db

def db_query(sql, params=None, fetchone=False, fetchall=False, commit=False):
    """Eksekusi query dengan parameterized binding (aman)."""
    conn = get_db()
    if USE_PG:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params or ())
        result = None
        if fetchone:   result = dict(cur.fetchone()) if cur.rowcount != 0 else None
        elif fetchall: result = [dict(r) for r in cur.fetchall()]
        if commit: conn.commit()
        conn.close()
        return result
    else:
        cur = conn.execute(sql, params or ())
        result = None
        if fetchone:   result = cur.fetchone()
        elif fetchall: result = cur.fetchall()
        if commit: conn.commit()
        return result

def db_query_raw(sql, fetchone=False, fetchall=False):
    """
    [VULN #1] Eksekusi RAW query tanpa sanitasi — SQL Injection!
    Dipanggil HANYA dari route login admin.
    """
    print(f"\n[DEBUG] SQL Query:\n  {sql}\n")
    conn = get_db()
    if USE_PG:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cur.execute(sql)
        except Exception:
            conn.close()
            return None
        result = None
        if fetchone:   result = dict(cur.fetchone()) if cur.pgresult_ptr else None
        elif fetchall: result = [dict(r) for r in cur.fetchall()]
        conn.close()
        return result
    else:
        try:
            cur = conn.execute(sql)
        except Exception:
            return None
        if fetchone:   return cur.fetchone()
        elif fetchall: return cur.fetchall()
        return None

@app.teardown_appcontext
def close_connection(exception):
    if not USE_PG:
        db = getattr(g, "_database", None)
        if db is not None:
            db.close()

# ── Routes ─────────────────────────────────────────────────────

# Halaman Home — Form Laporan
@app.route("/", methods=["GET", "POST"])
def index():
    success = False
    if request.method == "POST":
        nama  = request.form.get("nama_pelapor", "").strip()
        judul = request.form.get("judul", "").strip()
        isi   = request.form.get("isi_laporan", "").strip()
        if nama and judul and isi:
            # ======================================================
            # [VULN #2] STORED XSS — input disimpan tanpa sanitasi.
            # isi_laporan akan di-render dengan | safe di laporan.html
            # ======================================================
            db_query(
                f"INSERT INTO reports (nama_pelapor, judul, isi_laporan) VALUES ({PH},{PH},{PH})",
                (nama, judul, isi),
                commit=True
            )
            success = True
    return render_template("index.html", success=success)


# Halaman Daftar Laporan — Stored XSS execution point
@app.route("/laporan")
def daftar_laporan():
    laporan = db_query(
        "SELECT * FROM reports ORDER BY id DESC",
        fetchall=True
    ) or []
    return render_template("laporan.html", laporan=laporan)


# Admin Login — SQL Injection vulnerable
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # ======================================================
        # [VULN #1] SQL INJECTION — f-string tanpa parameterized query.
        # Payload bypass: admin' OR '1'='1' --
        # Query terbentuk:
        #   SELECT * FROM users WHERE username='admin' OR '1'='1' --'
        # Kondisi selalu TRUE → row pertama dikembalikan tanpa cek password.
        # ======================================================
        user = db_query(f"SELECT * FROM users WHERE username={PH}", (username,), fetchone=True)


        if user and check_password_hash(user["password"], password):

            session["admin_logged_in"] = True
            session["admin_user"]      = user["username"]
            session["sqli_used"]       = False
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Username atau password salah."

    return render_template("login.html", error=error)


# Admin Dashboard
@app.route("/admin")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    laporan = db_query("SELECT * FROM reports ORDER BY id DESC", fetchall=True) or []
    users   = db_query("SELECT id, username, password FROM users", fetchall=True) or []

    return render_template(
        "admin.html",
        laporan    = laporan,
        users      = users,
        total      = len(laporan),
        admin_user = session.get("admin_user"),
        sqli_used  = session.get("sqli_used", False),
    )


# Hapus Laporan
@app.route("/admin/hapus/<int:report_id>")
def hapus_laporan(report_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    db_query(f"DELETE FROM reports WHERE id = {PH}", (report_id,), commit=True)
    return redirect(url_for("admin_dashboard"))


# Edit Laporan
@app.route("/admin/edit/<int:report_id>", methods=["POST"])
def edit_laporan(report_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    nama  = request.form.get("nama_pelapor", "")
    judul = request.form.get("judul", "")
    isi   = request.form.get("isi_laporan", "")
    db_query(
        f"UPDATE reports SET nama_pelapor={PH}, judul={PH}, isi_laporan={PH} WHERE id={PH}",
        (nama, judul, isi, report_id),
        commit=True
    )
    return redirect(url_for("admin_dashboard"))


# Tambah Laporan (dari Admin)
@app.route("/admin/tambah", methods=["POST"])
def admin_tambah_laporan():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    nama  = request.form.get("nama_pelapor", "")
    judul = request.form.get("judul", "")
    isi   = request.form.get("isi_laporan", "")
    # [VULN #2] Stored XSS — input dari admin pun tidak disanitasi
    db_query(
        f"INSERT INTO reports (nama_pelapor, judul, isi_laporan) VALUES ({PH},{PH},{PH})",
        (nama, judul, isi),
        commit=True
    )
    return redirect(url_for("admin_dashboard"))


# Logout
@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("index"))



# ── Entry Point ────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
