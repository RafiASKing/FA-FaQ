import streamlit as st
import pandas as pd
import time
import re
from src import database, utils

# --- AUTH ---
# Password sederhana untuk demo
if 'auth' not in st.session_state: st.session_state.auth = False

def login():
    # Password hardcoded: "veven"
    if st.session_state.pass_input == "veven": 
        st.session_state.auth = True
    else:
        st.error("Password salah")

if not st.session_state.auth:
    st.set_page_config(page_title="Admin Login")
    st.markdown("<h1 style='text-align: center;'>🔒 Admin Login</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.text_input("Password", type="password", key="pass_input", on_change=login)
    st.stop()

# --- MAIN UI ---
st.set_page_config(page_title="Admin Console", layout="wide")
st.title("🛠️ Admin Console (Safe Mode)")
tags_map = utils.load_tags_config()

# State Management
if 'preview_mode' not in st.session_state: st.session_state.preview_mode = False
if 'draft_data' not in st.session_state: st.session_state.draft_data = {}

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 List Data", "➕ Tambah (Preview)", "✏️ Edit/Hapus", "⚙️ Config Tags"])

# === TAB 1: LIST DATA ===
with tab1:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear() # Clear cache agar data terbaru muncul
        st.rerun()
        
    df = database.get_all_data_as_df()
    st.dataframe(df, use_container_width=True, hide_index=True)

# === TAB 2: TAMBAH DATA (WORKFLOW) ===
with tab2:
    # --- PHASE 1: INPUT FORM ---
    if not st.session_state.preview_mode:
        st.info("💡 Tips: Gunakan [GAMBAR 1] di dalam jawaban untuk menyisipkan gambar.")
        
        col_m, col_j = st.columns([1, 3])
        with col_m: i_tag = st.selectbox("Modul", list(tags_map.keys()), key="in_t")
        with col_j: i_judul = st.text_input("Judul Masalah", key="in_j")
            
        i_jawab = st.text_area("Jawaban / Solusi", height=200, key="in_a", 
                              placeholder="Langkah 1: Klik tombol save.\n[GAMBAR 1]\n\nLangkah 2: Selesai.")
        
        i_key = st.text_input("Keyword Tambahan (Opsional)", key="in_k", placeholder="Contoh: error 505, puyer, resep")
        i_src = st.text_input("URL Sumber (ClickUp/PDF)", key="in_s")
        i_imgs = st.file_uploader("Upload Gambar", accept_multiple_files=True, key="in_i")
        
        if st.button("🔍 Lanjut ke Preview", type="primary"):
            if not i_judul or not i_jawab:
                st.error("Judul & Jawaban wajib diisi!")
            else:
                # Simpan draft di memori sementara
                st.session_state.draft_data = {
                    "tag": i_tag, "judul": i_judul, "jawab": i_jawab,
                    "key": i_key, "src": i_src, "imgs": i_imgs
                }
                st.session_state.preview_mode = True
                st.rerun()

    # --- PHASE 2: PREVIEW & SUBMIT ---
    else:
        draft = st.session_state.draft_data
        st.warning("⚠️ Mode Preview: Data belum disimpan ke Database.")
        
        c_back, c_save = st.columns([1, 4])
        with c_back:
            if st.button("⬅️ Edit Lagi"):
                st.session_state.preview_mode = False
                st.rerun()
        
        with c_save:
            # INI LOGIC PENTINGNYA
            if st.button("💾 SIMPAN DATA (PUBLISH)", type="primary"):
                try:
                    with st.spinner("Sedang menyimpan (Menunggu antrian DB)..."):
                        # 1. Simpan Gambar dulu ke Folder Lokal
                        paths = utils.save_uploaded_images(draft['imgs'], draft['judul'], draft['tag'])
                        
                        # 2. Simpan ke DB dengan ID "auto"
                        # Biarkan Backend yang menghitung urutan ID agar tidak bentrok
                        new_id = database.upsert_faq(
                            doc_id="auto", # KUNCINYA DISINI
                            tag=draft['tag'], 
                            judul=draft['judul'], 
                            jawaban=draft['jawab'], 
                            keyword=draft['key'], 
                            img_paths=paths, 
                            src_url=draft['src']
                        )
                        
                        st.success(f"✅ Sukses! Data tersimpan dengan ID: {new_id}")
                        st.session_state.preview_mode = False
                        st.session_state.draft_data = {}
                        database.get_all_data_as_df.clear() # Clear cache tabel
                        time.sleep(2)
                        st.rerun()
                except Exception as e: 
                    st.error(f"Gagal Menyimpan: {e}")

        # --- Tampilan Preview User ---
        st.divider()
        st.subheader("📱 Preview Tampilan User")
        
        hex_color = tags_map.get(draft['tag'], {}).get("color", "#808080")
        st.markdown(f"### <span style='color:{hex_color}'>[{draft['tag']}]</span> {draft['judul']}", unsafe_allow_html=True)
        
        # Render sederhana untuk preview
        parts = re.split(r'(\[GAMBAR\s*\d+\])', draft['jawab'], flags=re.IGNORECASE)
        imgs = draft['imgs'] or []
        
        for part in parts:
            match = re.search(r'\[GAMBAR\s*(\d+)\]', part, re.IGNORECASE)
            if match:
                try:
                    idx = int(match.group(1)) - 1
                    if 0 <= idx < len(imgs):
                        st.image(imgs[idx], width=300, caption=f"Gambar {idx+1}")
                    else:
                        st.caption(f"⚠️ Placeholder [GAMBAR {idx+1}] kosong")
                except: pass
            else:
                if part.strip(): st.markdown(part)

# === TAB 3: EDIT/HAPUS ===
with tab3:
    st.header("✏️ Edit Data Lama")
    df_e = database.get_all_data_as_df()
    
    if not df_e.empty:
        # Dropdown pilih data
        opts = [f"{r['ID']} | {r['Judul']}" for _, r in df_e.iterrows()]
        sel = st.selectbox("Pilih Data untuk Diedit", opts)
        
        if sel:
            sel_id = sel.split(" | ")[0]
            row = df_e[df_e['ID'] == sel_id].iloc[0]
            
            with st.form("edit_form"):
                curr = row['Tag']
                idx = list(tags_map.keys()).index(curr) if curr in tags_map else 0
                
                c_id, c_t = st.columns([1, 4])
                with c_id: st.text_input("ID (Locked)", value=sel_id, disabled=True)
                with c_t: e_tag = st.selectbox("Modul", list(tags_map.keys()), index=idx)
                
                e_jud = st.text_input("Judul", value=row['Judul'])
                e_jaw = st.text_area("Jawaban", value=row['Jawaban'], height=200)
                e_key = st.text_input("Keyword", value=row['Keyword'])
                e_src = st.text_input("Source URL", value=row['Source'])
                
                st.markdown(f"**Path Gambar Saat Ini:** `{row['Gambar']}`")
                st.info("Biarkan kosong jika tidak ingin mengubah gambar.")
                e_new = st.file_uploader("Ganti Gambar (Overwrite)", accept_multiple_files=True)
                
                c_up, c_del = st.columns([1, 1])
                
                # UPDATE BTN
                if c_up.form_submit_button("💾 UPDATE DATA"):
                    p = row['Gambar']
                    if e_new: 
                        p = utils.save_uploaded_images(e_new, e_jud, e_tag)
                    
                    # Panggil upsert dengan ID LAMA (Update Mode)
                    database.upsert_faq(sel_id, e_tag, e_jud, e_jaw, e_key, p, e_src)
                    
                    st.toast("Update Berhasil!", icon="✅")
                    database.get_all_data_as_df.clear()
                    time.sleep(1)
                    st.rerun()
                
                # DELETE BTN
                if c_del.form_submit_button("🗑️ HAPUS PERMANEN", type="primary"):
                    database.delete_faq(sel_id)
                    st.toast("Data Dihapus.", icon="🗑️")
                    database.get_all_data_as_df.clear()
                    time.sleep(1)
                    st.rerun()

# === TAB 4: CONFIG ===
with tab4:
    st.header("🎨 Pengaturan Tag & Warna")
    flat = [{"Tag":k, "Warna":v.get("color",""), "Desc":v.get("desc","")} 
            for k,v in tags_map.items()]
    st.dataframe(pd.DataFrame(flat), use_container_width=True, hide_index=True)
    
    with st.expander("➕ Tambah Tag Baru"):
        with st.form("conf_f", clear_on_submit=True):
            n_name = st.text_input("Nama Tag (ex: Farmasi)")
            n_col = st.selectbox("Warna Badge", list(utils.COLOR_PALETTE.keys()))
            n_desc = st.text_area("Deskripsi AI (Penting untuk search)")
            
            if st.form_submit_button("Simpan Tag"):
                if n_name:
                    hex_c = utils.COLOR_PALETTE[n_col]["hex"]
                    tags_map[n_name] = {"color": hex_c, "desc": n_desc}
                    utils.save_tags_config(tags_map)
                    st.toast("Tag Tersimpan!"); time.sleep(1); st.rerun()