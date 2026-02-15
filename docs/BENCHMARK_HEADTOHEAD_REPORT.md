# Head-to-Head Benchmark Report
> **Date**: 2026-02-15 (re-run) | **Queries**: 40 × 2 systems = 80 searches

---

## System Configurations

| | OLD System | NEW System |
|---|---|---|
| **Template** | `DOMAIN / DOKUMEN / VARIASI PERTANYAAN USER / ISI KONTEN` | `MODUL / TOPIK / TERKAIT / ISI KONTEN` |
| **Doc Embedding** | `RETRIEVAL_DOCUMENT` | `RETRIEVAL_DOCUMENT` |
| **Query Embedding** | `RETRIEVAL_DOCUMENT` (symmetric) | `RETRIEVAL_QUERY` (asymmetric) |
| **Score Formula** | `(1 - 2×cosine_dist) × 100` (ChromaDB L2²) | `(1 - cosine_dist) × 100` (Typesense cosine) |
| **Threshold** | 41% | 70% |
| **Embedding Model** | `gemini-embedding-001` (3072-dim) | `gemini-embedding-001` (3072-dim) |

---

## Overall Accuracy

| Metric | OLD (L2², 41%) | NEW (cosine, 70%) | Winner |
|--------|---------------|-------------------|--------|
| Relevant passed (recall) | 20/20 = 100% | 16/20 = 80% | ⬅️ OLD |
| Irrelevant rejected | 8/10 = 80% | 10/10 = 100% | ➡️ NEW |
| Tricky rejected | 3/10 = 30% | 7/10 = 70% | ➡️ NEW |
| **Overall accuracy** | 31/40 = 78% | 33/40 = 82% | ➡️ NEW |

---

## Per-Query: ✅ Relevant Queries (Should PASS)

| # | Query | OLD Score | OLD | OLD Retrieved | NEW Score | NEW | NEW Retrieved | Same? |
|---|-------|-----------|-----|---------------|-----------|-----|---------------|-------|
| 1 | tombol call pasien saya abu-abu gabisa diklik | 80.3% | ✅ PASS | Kenapa tombol "Call" pasien saya tidak bisa d | 85.1% | ✅ PASS | Kenapa tombol "Call" pasien saya tidak bisa d | ✅ |
| 2 | gabisa login di hp nurse ipd | 71.9% | ✅ PASS | Apa Penyebab Nurse Tidak Bisa Mengakses Nurse | 80.7% | ✅ PASS | Apa Penyebab Nurse Tidak Bisa Mengakses Nurse | ✅ |
| 3 | cara nambah resep obat di soap | 68.2% | ✅ PASS | Bagaimana cara menambahkan Resep Obat di sist | 81.5% | ✅ PASS | Bagaimana cara menambahkan Resep Obat di sist | ✅ |
| 4 | form apa aja yang belum ada di emr ed? | 77.5% | ✅ PASS | Apa saja form di EMR ED yang belum tercover? | 86.0% | ✅ PASS | Apa saja form di EMR ED yang belum tercover? | ✅ |
| 5 | kenapa discharge pasien error gabisa? | 75.1% | ✅ PASS | Kenapa tidak bisa Request Discharge Pasien di | 81.8% | ✅ PASS | Kenapa tidak bisa Request Discharge Pasien di | ✅ |
| 6 | data yang wajib diisi di soap itu apa aja? | 71.1% | ✅ PASS | Data apa saja yang wajib (mandatory) diisi pa | 81.4% | ✅ PASS | Data apa saja yang wajib (mandatory) diisi pa | ✅ |
| 7 | template soap rehab kok gak ada therapy plan? | 82.8% | ✅ PASS | Kenapa pada Template SOAP tidak ada inputan " | 87.5% | ✅ PASS | Kenapa pada Template SOAP tidak ada inputan " | ✅ |
| 8 | bisa gak order obat sebelum asesmen perawat? | 72.8% | ✅ PASS | Apakah bisa order obat sebelum pengkajian per | 81.6% | ✅ PASS | Apakah bisa order obat sebelum pengkajian per | ✅ |
| 9 | cashier mau print form lab dari igd bisa gak? | 73.4% | ✅ PASS | Apakah cashier bisa print dokumen order/hasil | 82.4% | ✅ PASS | Apakah cashier bisa print dokumen order/hasil | ✅ |
| 10 | obat drip bisa diresepkan gak? | 68.4% | ✅ PASS | Apakah bisa melakukan peresepan untuk obat dr | 79.8% | ✅ PASS | Apakah bisa melakukan peresepan untuk obat dr | ✅ |
| 11 | obat | 53.3% | ✅ PASS | Bagaimana cara menambahkan Resep Obat di sist | 69.4% | ❌ FAIL | Bagaimana cara menambahkan Resep Obat di sist | ✅ |
| 12 | form ed | 54.4% | ✅ PASS | Apa saja form di EMR ED yang belum tercover? | 71.8% | ✅ PASS | Apa saja form di EMR ED yang belum tercover? | ✅ |
| 13 | discharge | 50.8% | ✅ PASS | Kenapa tidak bisa Request Discharge Pasien di | 71.9% | ✅ PASS | Kenapa tidak bisa Request Discharge Pasien di | ✅ |
| 14 | call pasien | 64.7% | ✅ PASS | Kenapa tombol "Call" pasien saya tidak bisa d | 77.4% | ✅ PASS | Kenapa tombol "Call" pasien saya tidak bisa d | ✅ |
| 15 | resep | 51.3% | ✅ PASS | Bagaimana cara menambahkan Resep Obat di sist | 69.1% | ❌ FAIL | Bagaimana cara menambahkan Resep Obat di sist | ✅ |
| 16 | referral | 48.1% | ✅ PASS | Apakah bisa mengubah jenis Referral Konsultas | 63.9% | ❌ FAIL | Apakah bisa mengubah jenis Referral Konsultas | ✅ |
| 17 | mcu | 49.4% | ✅ PASS | Apakah mcu bisa pakai bni life? | 71.3% | ✅ PASS | Apakah mcu bisa pakai bni life? | ✅ |
| 18 | soap | 50.0% | ✅ PASS | Data apa saja yang wajib (mandatory) diisi pa | 70.2% | ✅ PASS | Data apa saja yang wajib (mandatory) diisi pa | ✅ |
| 19 | nurse ipd | 56.1% | ✅ PASS | Apa Penyebab Nurse Tidak Bisa Mengakses Nurse | 76.9% | ✅ PASS | Apa Penyebab Nurse Tidak Bisa Mengakses Nurse | ✅ |
| 20 | print lab | 52.8% | ✅ PASS | Bagaimana cara print order laboratory emergen | 67.7% | ❌ FAIL | Apakah cashier bisa print dokumen order/hasil | ⚡ DIFF |

> **Different retrievals**: 1/20 queries retrieved a different top FAQ between OLD and NEW.

---

## Per-Query: ❌ Irrelevant Queries (Should FAIL)

| # | Query | OLD Score | OLD | OLD Retrieved | NEW Score | NEW | NEW Retrieved | Same? |
|---|-------|-----------|-----|---------------|-----------|-----|---------------|-------|
| 1 | makan nasi padang yok | 43.3% | ❌ LEAK | Initial Asessment | 61.7% | ✅ FAIL | Initial Asessment | ✅ |
| 2 | sate kambing enak banget | 38.8% | ✅ FAIL | Initial Asessment | 60.1% | ✅ FAIL | Data apa saja yang wajib (mandatory) diisi pa | ⚡ DIFF |
| 3 | siapa presiden indonesia sekarang? | 45.5% | ❌ LEAK | Initial Asessment | 59.4% | ✅ FAIL | SHKJ apa? | ⚡ DIFF |
| 4 | harga tiket pesawat jakarta bali | 38.9% | ✅ FAIL | Apakah mcu bisa pakai bni life? | 60.2% | ✅ FAIL | SHKJ apa? | ⚡ DIFF |
| 5 | resep kue brownies coklat | 39.2% | ✅ FAIL | Bagaimana cara menambahkan Resep Obat di sist | 59.8% | ✅ FAIL | Bagaimana cara menambahkan Resep Obat di sist | ✅ |
| 6 | berapa harga iphone 16 pro max? | 40.3% | ✅ FAIL | Initial Asessment | 54.7% | ✅ FAIL | Salary Karyawan | ⚡ DIFF |
| 7 | manchester united menang berapa? | 39.5% | ✅ FAIL | Apakah mcu bisa pakai bni life? | 59.0% | ✅ FAIL | Apakah mcu bisa pakai bni life? | ✅ |
| 8 | nasi padang | 40.3% | ✅ FAIL | Initial Asessment | 60.8% | ✅ FAIL | Initial Asessment | ✅ |
| 9 | bola | 38.5% | ✅ FAIL | Apa saja form di EMR ED yang belum tercover? | 63.3% | ✅ FAIL | Apa saja form di EMR ED yang belum tercover? | ✅ |
| 10 | musik | 29.0% | ✅ FAIL | Initial Asessment | 58.2% | ✅ FAIL | Bagaimana Cara Mengedit Obat di EMR ED Pharma | ⚡ DIFF |

> **Different retrievals**: 5/10 queries retrieved a different top FAQ between OLD and NEW.

---

## Per-Query: ⚠️ Tricky Queries (Hospital-sounding, No FAQ — Should FAIL)

| # | Query | OLD Score | OLD | OLD Retrieved | NEW Score | NEW | NEW Retrieved | Same? |
|---|-------|-----------|-----|---------------|-----------|-----|---------------|-------|
| 1 | cara reset password emr saya lupa | 56.2% | ❌ LEAK | Kenapa tidak bisa Request Discharge Pasien di | 70.4% | ❌ LEAK | Bagaimana Cara Mengedit Obat di EMR ED Pharma | ⚡ DIFF |
| 2 | bagaimana cara transfer pasien antar ruangan? | 55.0% | ❌ LEAK | Initial Asessment | 69.1% | ✅ FAIL | Initial Asessment | ✅ |
| 3 | dimana menu untuk input hasil radiologi? | 59.0% | ❌ LEAK | Apakah cashier bisa print dokumen order/hasil | 73.0% | ❌ LEAK | Apakah cashier bisa print dokumen order/hasil | ✅ |
| 4 | cara bikin surat rujukan BPJS | 53.8% | ❌ LEAK | Apakah bisa mengubah jenis Referral Konsultas | 67.1% | ✅ FAIL | Apakah bisa mengubah jenis Referral Konsultas | ✅ |
| 5 | gimana caranya booking ruang operasi? | 52.1% | ❌ LEAK | Kenapa tombol "Call" pasien saya tidak bisa d | 68.8% | ✅ FAIL | Kenapa tombol "Call" pasien saya tidak bisa d | ✅ |
| 6 | jadwal dokter | 62.6% | ❌ LEAK | Bagaimana saya lihat list pasien dikemudian h | 73.5% | ❌ LEAK | Bagaimana saya lihat list pasien dikemudian h | ✅ |
| 7 | reset password | 39.2% | ✅ FAIL | Initial Asessment | 59.3% | ✅ FAIL | Initial Asessment | ✅ |
| 8 | radiologi | 40.9% | ✅ FAIL | Apakah cashier bisa print dokumen order/hasil | 67.2% | ✅ FAIL | Apakah cashier bisa print dokumen order/hasil | ✅ |
| 9 | bpjs | 39.1% | ✅ FAIL | Salary Karyawan | 67.4% | ✅ FAIL | Kenapa tombol "Call" pasien saya tidak bisa d | ⚡ DIFF |
| 10 | transfer pasien | 53.1% | ❌ LEAK | Kenapa tidak bisa Request Discharge Pasien di | 69.4% | ✅ FAIL | Kenapa tidak bisa Request Discharge Pasien di | ✅ |

> **Different retrievals**: 2/10 queries retrieved a different top FAQ between OLD and NEW.

---

## Conclusion

| Aspect | OLD | NEW | Verdict |
|--------|-----|-----|---------|
| **Overall accuracy** | 78% | 82% | ➡️ NEW |
| **Catches relevant** | 100% | 80% | ⬅️ OLD |
| **Blocks irrelevant** | 80% | 100% | ➡️ NEW |
| **Blocks tricky** | 30% | 70% | ➡️ NEW |

> **Total queries where OLD and NEW retrieved different FAQs**: 8/40