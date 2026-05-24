"""
init_supabase.py
Jalankan SEKALI untuk membuat tabel dan seed data di Supabase.

Usage:
  set DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
  python init_supabase.py
"""

import os
import psycopg2
from werkzeug.security import generate_password_hash

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("[ERROR] Set environment variable DATABASE_URL terlebih dahulu!\n"
                     "Contoh:\n"
                     "  set DATABASE_URL=postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres")

print(f"[*] Connecting ke Supabase...")
conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cur  = conn.cursor()

# ── Drop & Create Tables ─────────────────────────────────────
print("[*] Membuat skema tabel...")
cur.execute("DROP TABLE IF EXISTS reports;")
cur.execute("DROP TABLE IF EXISTS users;")

cur.execute("""
    CREATE TABLE users (
        id       SERIAL PRIMARY KEY,
        username TEXT   NOT NULL UNIQUE,
        password TEXT   NOT NULL
    );
""")

cur.execute("""
    CREATE TABLE reports (
        id           SERIAL PRIMARY KEY,
        nama_pelapor TEXT NOT NULL,
        judul        TEXT NOT NULL,
        isi_laporan  TEXT NOT NULL
    );
""")
print("[+] Tabel users & reports berhasil dibuat.")

# ── Seed Users (hashed passwords) ────────────────────────────
print("[*] Menyisipkan data users dengan password hash...")
accounts = [
    ("admin",     "admin123"),
    ("moderator", "mod2024"),
]
for username, plaintext in accounts:
    pw_hash = generate_password_hash(plaintext)
    cur.execute(
        "INSERT INTO users (username, password) VALUES (%s, %s);",
        (username, pw_hash)
    )
    print(f"    [+] {username} -> {pw_hash[:60]}...")

# ── Seed Reports ──────────────────────────────────────────────
print("[*] Menyisipkan laporan contoh...")
seed_reports = [
    ("Budi Santoso",  "Lampu Jalan Mati",  "Lampu jalan di Gang Mawar RT 05 sudah mati selama 2 minggu."),
    ("Siti Rahayu",   "Jalan Berlubang",   "Jalan utama depan SDN 01 berlubang sangat dalam, berbahaya untuk pengendara motor."),
    ("Andi Wijaya",   "Sampah Menumpuk",   "Tumpukan sampah di depan Pasar Lama tidak pernah diangkut lebih dari seminggu."),
]
for nama, judul, isi in seed_reports:
    cur.execute(
        "INSERT INTO reports (nama_pelapor, judul, isi_laporan) VALUES (%s, %s, %s);",
        (nama, judul, isi)
    )
    print(f"    [+] {judul}")

conn.commit()
cur.close()
conn.close()

print("\n[OK] Supabase database siap!")
print("[!]  PERINGATAN: Aplikasi ini SENGAJA rentan. Hanya untuk edukasi CTF!")
