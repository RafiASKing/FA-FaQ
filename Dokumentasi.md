</dokumentasi_perjalanan_pengembangan>

Berikut adalah dokumen **Rekap Evolusi Teknis & Architecture Decision Record (ADR)** yang telah dirapikan. Dokumen ini menggabungkan seluruh riwayat pengembangan, mulai dari kendala awal hingga solusi "Golden Master" saat ini.

---

# 🚀 Journey of Development: Fast Cognitive Search System 

Dokumen ini merekam evolusi teknis sistem, mencakup masalah yang dihadapi, keputusan arsitektur yang diambil, dan alasan strategis di baliknya.

---

## 🧠 Bagian 1: Core Intelligence & Search Logic (Otak Sistem)

Fokus pada akurasi pencarian, efisiensi AI, dan relevansi jawaban medis.

### 1.1. Logika Filtering (Pre-Filtering vs Post-Filtering)
*   **Masalah:** Awalnya menggunakan *Post-Filtering* (Cari Top 10 global dulu, baru saring Tag).
    *   *Risiko:* Jika user mencari "Obat" tapi filter "IGD", dan Top 10 didominasi "Farmasi", hasil IGD menjadi kosong padahal datanya ada di ranking 11.
*   **Keputusan:** Implementasi **Pre-Filtering (Native ChromaDB `where` clause)**.
*   **Mekanisme:** Sistem menyaring tumpukan data berdasarkan Tag *sebelum* AI melakukan ranking semantic.
*   **Benefit:** **Akurasi 100%**. User medis dijamin menemukan data spesifik modul (misal: ED/IGD) jika data memang tersedia.

### 1.2. Penanganan Noise AI (Data Quality)
*   **Masalah:** Kode visual seperti `[GAMBAR 1]` ikut di-embed ke AI. Akibatnya, jika user mencari kata "Gambar", semua artikel muncul di ranking atas (Hallucination by Keyword).
*   **Keputusan:** Implementasi **Text Cleaner (`clean_text_for_embedding`)**.
*   **Mekanisme:** Teks yang dikirim ke Gemini dibersihkan dari tag gambar, namun tetap mempertahankan Markdown penting.
*   **Benefit:** AI murni fokus pada **konteks medis** (gejala, solusi, error code), bukan instruksi visual.

### 1.3. Latency & Performance (Caching)
*   **Masalah:** Sistem melakukan *re-run* embedding ke Google API setiap kali user mengganti filter, menyebabkan *lag* 0.5 - 1 detik dan boros kuota.
*   **Keputusan:** Implementasi **Caching Strategy (`@st.cache_data`)**.
*   **Benefit:** Pergantian filter kini **INSTANT (0 detik)** dan menghemat biaya API call secara signifikan.

### 1.4. Confidence Threshold (Pencegahan Halusinasi)
*   **Masalah:** Sistem "memaksa" memberikan jawaban meskipun user mengetik kata acak/kasar, berpotensi memberikan info medis yang salah.
*   **Keputusan:** Menambahkan **Confidence Threshold (>25%)**.
*   **Benefit:** Lebih baik sistem menjawab "Tidak ditemukan" daripada memberikan jawaban yang menyesatkan di lingkungan rumah sakit.

### 1.5. Universal Semantic Structure (Manual HyDE Strategy)
*   **Masalah:** Terjadi *Semantic Gap* (Kesenjangan Bahasa) antara User dan Dokumen.
    *   *Contoh:* User mengetik bahasa panik/slang ("Gak bisa masuk", "Tombol mati"), sedangkan Dokumen menggunakan bahasa teknis/baku ("Gagal Autentikasi", "Sistem Offline").
    *   *Risiko:* AI gagal mencocokkan keduanya karena kosa katanya terlalu berbeda, meskipun maksudnya sama.
*   **Keputusan:** Implementasi **Structured Embedding dengan Strategi HyDE (Hypothetical Document Embeddings)**.
*   **Mekanisme:**
    *   Mengubah struktur teks yang di-embed dari sekadar gabungan teks menjadi format semantik yang tegas:
        ```text
        DOMAIN: ED (IGD, Emergency)  <-- Konteks Modul + Sinonim
        DOKUMEN: Cara Login          <-- Judul Resmi
        VARIASI PERTANYAAN USER: Gak bisa masuk, Lupa password <-- Bahasa User (HyDE)
        ISI KONTEN: ...              <-- Solusi Teknis
        ```
    *   Admin diinstruksikan mengisi kolom "Keyword" dengan **variasi pertanyaan user**, bukan sekadar kata kunci kaku.
*   **Benefit:**
    1.  **Telepathic Search:** Sistem mengerti "Bahasa Lapangan" user.
    2.  **Universal Robustness:** Struktur ini agnostik (tidak terikat RS), siap digunakan untuk domain lain (Banking, HR, Logistik) tanpa ubah kodingan.

---

## 🎨 Bagian 2: User Experience (Interface & Flow)

Fokus pada kemudahan penggunaan bagi perawat/dokter dan kejelasan informasi.

### 2.1. Mengatasi "Blank Screen Syndrome"
*   **Masalah:** Saat aplikasi dibuka, layar kosong hanya berisi search bar. User baru bingung harus melakukan apa.
*   **Keputusan:** Implementasi **Browse Mode (Mode Jelajah)**.
*   **Mekanisme:** Jika search bar kosong $\rightarrow$ Tampilkan data terbaru (ID Terbesar). Jika terisi $\rightarrow$ Masuk Search Mode.
*   **Benefit:** Meningkatkan *discoverability*. User langsung melihat update SOP terbaru tanpa perlu mengetik.

### 2.2. Struktur Visual (Hybrid Inline Image)
*   **Masalah:** Gambar menumpuk di bawah teks (Galeri). Sulit dipahami untuk SOP langkah-demi-langkah.
*   **Keputusan:** Fitur **Inline Image (`[GAMBAR X]`)**.
*   **Mekanisme:** Gambar diselipkan secara natural di antara paragraf teks.
*   **Benefit:** Instruksi menjadi runut dan mudah dibaca (Teks -> Gambar -> Teks).

### 2.3. Explainable AI (Transparansi)
*   **Masalah:** User tidak tahu apakah hasil pencarian ini valid atau sekadar keyword matching.
*   **Keputusan:** Menambahkan **Confidence Score Badge**.
*   **Mekanisme:** Menampilkan persentase relevansi dengan kode warna (Hijau/Orange/Merah).
*   **Benefit:** Memberikan efek psikologis "Trust" kepada user bahwa sistem benar-benar "berpikir".

### 2.4. Navigasi & Scalability
*   **Masalah:** Menampilkan 50+ hasil sekaligus membuat UI panjang (*Infinite Scroll*) dan berat.
*   **Keputusan:** Implementasi **Pagination System** (10 item per halaman).
*   **Benefit:** UI bersih, ringan, dan terlihat profesional.

### 2.5. Visual Consistency (Single Source of Truth)
*   **Masalah:** Awalnya warna badge (label kategori) di-hardcode di dalam script.
    *   *Risiko 1:* Jika Admin ingin mengubah warna "IGD" dari Merah ke Biru, harus memanggil programmer untuk edit kode.
    *   *Risiko 2:* Tanpa pembatasan, Admin mungkin memilih warna yang merusak kontras (misal: teks putih di background kuning terang).
*   **Keputusan:** Implementasi **Dynamic JSON Configuration (`tags_config.json`)** dengan **Restricted Palette**.
*   **Mekanisme:**
    *   App User dan Admin membaca file konfigurasi yang sama di folder `data/`.
    *   Pilihan warna di Admin **dibatasi** pada palet resmi (Merah, Hijau, Biru, Orange, Ungu, Abu) yang sudah dikalibrasi agar enak dilihat.
*   **Benefit:**
    1.  **Konsistensi:** User tidak bingung dengan warna-warni liar.
    2.  **Fleksibilitas:** Admin bisa menambah/mengedit modul tanpa menyentuh satu baris kode pun.

### 2.6. Closed Loop Support (Contextual Call-to-Action)
*   **Masalah:** Pesan error "Data Tidak Ditemukan" adalah jalan buntu (*Dead End*). User frustrasi dan masalah tidak terselesaikan.
*   **Keputusan:** Integrasi **Direct Support Link (WhatsApp Bot)** pada kondisi *No Result*.
*   **Mekanisme:**
    *   Jika relevansi < 25%, sistem menampilkan tombol "Chat WhatsApp Support".
    *   **Auto-Fill Message:** Link WA otomatis terisi dengan draf pesan: *"Halo Admin, saya cari solusi tentang [Query User] tapi tidak ketemu..."*
*   **Benefit:**
    1.  **Psikologis:** User merasa "diurus" meskipun jawaban belum ada di database.
    2.  **Ticket Automation:** Tim IT langsung mendapat laporan spesifik tentang apa yang dicari user, mempercepat perbaikan konten (Feedback Loop Aktif).

---

## 🛠️ Bagian 3: Admin Workflow & Operations

Fokus pada keamanan data, kemudahan input, dan feedback loop.

### 3.1. Zero-Error Input Workflow
*   **Masalah:** Admin melakukan *Blind Input* (Langsung Save tanpa tahu hasil jadinya), rawan typo format.
*   **Keputusan:** Menambahkan **Preview Mode** sebelum Submit.
*   **Benefit:** Admin bisa memvalidasi tampilan visual sebelum data dipublish ke User.

### 3.2. Smart Typing Experience
*   **Masalah:** Admin harus mengetik kode `[GAMBAR 1]` secara manual. Rawan salah ketik dan melelahkan.
*   **Keputusan:** Implementasi **Smart Toolbar (📸 Auto-Counter)**.
*   **Mekanisme:** Satu tombol pintar yang otomatis menghitung urutan gambar dan menyisipkan tag yang sesuai.
*   **Benefit:** UX *Don't make me think*. Mempercepat proses input data hingga 2x lipat.

### 3.3. Data Safety (Anti-Amnesia)
*   **Masalah:** Jika Admin menekan tombol "Edit Lagi" atau reload, data yang sudah diketik hilang.
*   **Keputusan:** Implementasi **Session State Draft**.
*   **Benefit:** Menjaga *mental state* admin. Data input persisten sampai benar-benar disimpan.

### 3.4. Feedback Loop (Analytics)
*   **Masalah:** Admin tidak tahu apa yang dicari user namun belum ada jawabannya di database.
*   **Keputusan:** Fitur **Log Pencarian Gagal (Analytics Tab)**.
*   **Benefit:** *Data Driven Development*. Admin membuat konten baru berdasarkan kebutuhan riil di lapangan.

### 3.5. Maintenance (Zombie Cleaner)
*   **Masalah:** Menghapus data di database tidak menghapus file gambar di folder server (Storage Leak).
*   **Keputusan:** Logic **Deep Delete** (Hapus DB = Hapus File Fisik).
*   **Benefit:** Server tetap bersih dari file sampah (*maintenance free*).

---

## 🏗️ Bagian 4: Architecture & Robustness

Fokus pada fondasi teknis, keamanan, dan deployment.

### 4.1. Security Standard
*   **Masalah:** API Key dan Password hardcoded di dalam script. Berisiko tinggi jika source code bocor.
*   **Keputusan:** Migrasi ke **Environment Variables (`.env`)**.
*   **Benefit:** Memenuhi standar keamanan Enterprise.

### 4.2. Code Structure (Modularity)
*   **Masalah:** Kode awal berupa *Spaghetti Code* (semua dalam satu file).
*   **Keputusan:** Refactoring ke struktur **Modular** (`src/database`, `src/utils`, `src/config`).
*   **Benefit:** Mudah dibaca, mudah di-maintenance, dan siap untuk migrasi ke framework lebih besar (FastAPI) di masa depan.

### 4.3. Concurrency Handling
*   **Masalah:** Database SQLite sering *crash* ("Locked") jika diakses banyak user bersamaan.
*   **Keputusan:** Implementasi **`@retry_on_lock` Decorator dengan Jitter**.
*   **Benefit:** Sistem menjadi *robust* (tahan banting) menangani antrian request tanpa perlu setup database server yang berat.

---

## 📊 Ringkasan: Before vs After

| Aspek | Status Awal (Before) | Status Final (Golden Master) |
| :--- | :--- | :--- |
| **Logic Search** | Post-Filter (Rawan Data Hilang) | **Pre-Filter (Akurasi 100%)** |
| **AI Context** | Tercemar Noise Visual | **Bersih (Text Cleaner)** |
| **Embedding Strategy** | Flat Text (Rawan Meleset) | **Structured HyDE (Universal & Robust)** |
| **Tampilan User** | Blank Screen & Galeri Menumpuk | **Browse Mode & Inline Image** |
| **Handling No Result** | Jalan Buntu (Pesan Error) | **Call-to-Action (WhatsApp Integration)** |
| **Admin Input** | Manual & Rawan Typo | **Smart Toolbar & Preview Mode** |
| **Keamanan** | Hardcoded Credentials | **Environment Variables (.env)** |
| **Stabilitas** | Rawan Crash (SQLite Locked) | **Robust (Retry Mechanism)** |

---

### ✅ Status Sistem Saat Ini
Sistem telah berevolusi dari sekadar *Prototype* menjadi aplikasi **Production-Ready** skala departemen dengan karakteristik:
1.  **High Accuracy:** Logika pencarian yang matang.
2.  **User Centric:** Interface yang memandu user.
3.  **Low Maintenance:** Fitur pembersihan otomatis dan logging.
4.  **Secure:** Pemisahan kredensial dari kode.

</dokumentasi_perjalanan_pengembangan>


</next_pengembangan>
Bot WA
</next_pengembangan>



Berikut untuk codesnya yang terbaru:

<kode_baru>



</kode_baru>

Kira-kira seperti ini projectku. apakah siap untuk dilombakan? tinggal 1 minggu lagi ini btw, hehe....

