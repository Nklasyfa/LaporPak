-- ============================================================
-- LaporAman CTF — Supabase (PostgreSQL) Schema
-- Jalankan script ini di Supabase SQL Editor:
-- Dashboard → SQL Editor → New Query → Paste → Run
-- ============================================================

-- Hapus tabel lama jika ada
DROP TABLE IF EXISTS reports;
DROP TABLE IF EXISTS users;

-- Tabel users (admin)
CREATE TABLE users (
    id       SERIAL PRIMARY KEY,
    username TEXT   NOT NULL UNIQUE,
    password TEXT   NOT NULL
);

-- Tabel reports (laporan masyarakat)
CREATE TABLE reports (
    id           SERIAL PRIMARY KEY,
    nama_pelapor TEXT NOT NULL,
    judul        TEXT NOT NULL,
    isi_laporan  TEXT NOT NULL
);

-- ============================================================
-- Seed Data Users
-- Hash scrypt dari werkzeug:
--   admin     → admin123
--   moderator → mod2024
-- CATATAN: Login normal GAGAL (hash tidak diverifikasi di query SQLi).
--          Gunakan bypass: admin' OR '1'='1' --
-- ============================================================
INSERT INTO users (username, password) VALUES
(
  'admin',
  'scrypt:32768:8:1$WMi8LfLltBp4SKUY$2e0b141bf6efa993fc58fda558cec8aebb831ef6b809a6b0dcda2565b5f630bb52c45106e5e945c4b95a22846c00c3516b1c3d3de91662d8a2caa55a019d04cf'
),
(
  'moderator',
  'scrypt:32768:8:1$XJUFSJ6rLOwbvYml$88c57eb931318544ee0738249d56b8ca67147612b9c96f58138e6de510c63c55bb3ae036e9563014887a5f3cd3763961f9e79775aff8a74b14915d35272da25a'
);

-- ============================================================
-- Seed Data Reports (contoh laporan publik)
-- ============================================================
INSERT INTO reports (nama_pelapor, judul, isi_laporan) VALUES
('Budi Santoso', 'Lampu Jalan Mati',   'Lampu jalan di Gang Mawar RT 05 sudah mati selama 2 minggu.'),
('Siti Rahayu',  'Jalan Berlubang',    'Jalan utama depan SDN 01 berlubang sangat dalam, berbahaya untuk pengendara motor.'),
('Andi Wijaya',  'Sampah Menumpuk',    'Tumpukan sampah di depan Pasar Lama tidak pernah diangkut lebih dari seminggu.');
