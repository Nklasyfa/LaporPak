"""
============================================================
  LaporAman — Init Database (v2: Password Hashing)
  Jalankan: python init_db.py
============================================================
  Password disimpan sebagai hash (werkzeug pbkdf2-sha256).
  Ini menunjukkan: hashing password melindungi dari DB dump,
  TAPI tidak melindungi dari SQL Injection bypass!
============================================================
"""

import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = "laporaman.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_pelapor TEXT NOT NULL,
    judul        TEXT NOT NULL,
    isi_laporan  TEXT NOT NULL
);
"""

def init_db():
    import os
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"[*] Database lama dihapus: {DB_PATH}")

    print(f"[*] Membuat database baru: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executescript(SCHEMA)
    print("[+] Skema tabel berhasil dibuat.")

    # ================================================================
    # Password di-HASH menggunakan werkzeug (pbkdf2:sha256)
    # Ini mensimulasikan praktik keamanan yang BENAR untuk password storage.
    #
    # Demonstrasi CTF:
    #   - Jika DB bocor via SQLi UNION attack → attacker dapat hash, bukan plaintext
    #   - Hash sulit di-crack langsung (perlu brute-force/rainbow table)
    #   - TAPI SQLi Login Bypass (OR '1'='1') tetap berhasil karena
    #     bypass dilakukan di QUERY LEVEL, bukan password level!
    # ================================================================
    hashed_admin = generate_password_hash("admin123")
    hashed_mod   = generate_password_hash("mod2024")

    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        ("admin", hashed_admin)
    )
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        ("moderator", hashed_mod)
    )

    # Laporan seed (data bersih)
    seed_reports = [
        ("Budi Santoso",  "Lampu Jalan Mati",    "Lampu jalan di Gang Melati sudah mati selama 2 minggu, mohon segera diperbaiki."),
        ("Siti Rahayu",   "Jalan Berlubang",      "Jalan utama depan SDN 04 banyak lubang besar, sangat berbahaya bagi pengendara motor."),
        ("Andi Wijaya",   "Sampah Menumpuk",      "Tumpukan sampah di TPS Kelurahan Mawar tidak diangkut selama 5 hari."),
    ]
    cursor.executemany(
        "INSERT INTO reports (nama_pelapor, judul, isi_laporan) VALUES (?, ?, ?)",
        seed_reports
    )
    conn.commit()

    # Verifikasi
    users   = cursor.execute("SELECT id, username, password FROM users").fetchall()
    reports = cursor.execute("SELECT id, nama_pelapor, judul FROM reports").fetchall()

    print(f"\n[*] Data Users ({len(users)} akun) — perhatikan password sudah di-HASH:")
    for u in users:
        print(f"    ID={u[0]} | username={u[1]}")
        print(f"           password={u[2][:60]}...")

    print(f"\n[*] Data Reports ({len(reports)} laporan):")
    for r in reports:
        print(f"    ID={r[0]} | {r[1]} | {r[2]}")

    conn.close()
    print("\n[OK] Database siap. Jalankan: python app.py")
    print("[!]  PERINGATAN: Aplikasi ini SENGAJA rentan. Hanya untuk edukasi CTF!")

if __name__ == "__main__":
    init_db()
