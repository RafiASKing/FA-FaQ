import streamlit as st
import pandas as pd
import time
import re # Penting untuk preview manual
from src import database, utils

# --- AUTH ---
if 'auth' not in st.session_state: st.session_state.auth = False

def login():
    if st.session_state.pass_input == "veven": 
        st.session_state.auth = True
    else:
        st.error("Password salah")

if not st.session_state.auth:
    st.title("🔒 Admin Login")
    st.text_input("Password", type="password", key="pass_input", on_change=login)
    st.stop()

# --- MAIN UI ---
st.title("🛠️ Admin Console")
tags_map = utils.load_tags_config()

# State Management
if 'preview_mode' not in st.session_state: st.session_state.preview_mode = False
if 'draft_data' not in st.session_state: st.session_state.draft_data = {}

tab1, tab2, tab3, tab4 = st.tabs(["📊 List Data", "➕ Tambah (Preview)", "✏️ Edit/Hapus", "⚙️ Config Tags"])

# === TAB 1: LIST ===
with tab1:
    df = database.get_all_data_as_df()
    st.dataframe(df, use_container_width=True, hide_index=True)

# === TAB 2: TAMBAH DATA (WORKFLOW) ===
with tab2:
    # --- PHASE 1: INPUT FORM ---
    if not st.session_state.preview_mode:
        st.info("Input data baru di sini. Gunakan preview sebelum menyimpan.")
        
        with st.expander("ℹ️ Cheat Sheet Markdown & Gambar (Klik)"):
            st.markdown("""
            **Format Teks:**
            - **Tebal**: `**teks**`
            - List: `- isi` atau `1. isi`
            
            **Sisip Gambar:**
            - Ketik `[GAMBAR 1]` untuk gambar urutan ke-1.
            - Ketik `[GAMBAR 2]` untuk gambar urutan ke-2.
            - Jika kosong, gambar muncul di bawah.
            """)

        col_m, col_j = st.columns([1, 3])
        with col_m: i_tag = st.selectbox("Modul", list(tags_map.keys()), key="in_t")
        with col_j: i_judul = st.text_input("Judul", key="in_j")
            
        i_jawab = st.text_area("Jawaban", height=200, key="in_a", 
                              placeholder="Langkah 1: Klik tombol.\n[GAMBAR 1]\n\nLangkah 2: Selesai.")
        
        i_key = st.text_input("Keyword", key="in_k")
        i_src = st.text_input("URL Sumber", key="in_s")
        i_imgs = st.file_uploader("Upload Gambar", accept_multiple_files=True, key="in_i")
        
        if st.button("🔍 Lanjut ke Preview", type="primary"):
            if not i_judul or not i_jawab:
                st.error("Judul & Jawaban wajib diisi!")
            else:
                st.session_state.draft_data = {
                    "tag": i_tag, "judul": i_judul, "jawab": i_jawab,
                    "key": i_key, "src": i_src, "imgs": i_imgs
                }
                st.session_state.preview_mode = True
                st.rerun()

    # --- PHASE 2: PREVIEW & SUBMIT ---
    else:
        draft = st.session_state.draft_data
        st.warning("⚠️ Mode Preview: Data belum disimpan.")
        
        c_back, c_save = st.columns([1, 4])
        with c_back:
            if st.button("⬅️ Edit"):
                st.session_state.preview_mode = False
                st.rerun()
        
        with c_save:
            if st.button("💾 SIMPAN KE DATABASE", type="primary"):
                try:
                    with st.spinner("Menyimpan..."):
                        paths = utils.save_uploaded_images(draft['imgs'], draft['judul'], draft['tag'])
                        coll = database.get_collection()
                        safe_id = utils.get_next_id_safe(coll)
                        
                        database.upsert_faq(safe_id, draft['tag'], draft['judul'], 
                                          draft['jawab'], draft['key'], paths, draft['src'])
                        
                        st.toast(f"✅ Data ID {safe_id} Tersimpan!", icon="🎉")
                        st.session_state.preview_mode = False
                        st.session_state.draft_data = {}
                        time.sleep(1.5)
                        st.rerun()
                except Exception as e: st.error(f"Error: {e}")

        st.divider()
        st.subheader("📱 Tampilan User (Preview)")
        
        # Simulate Card
        hex_color = tags_map.get(draft['tag'], {}).get("color", "#808080")
        st.markdown(f"### <span style='color:{hex_color}'>[{draft['tag']}]</span> {draft['judul']}", unsafe_allow_html=True)
        
        # Manual Preview Render Logic
        parts = re.split(r'(\[GAMBAR\s*\d+\])', draft['jawab'], flags=re.IGNORECASE)
        imgs = draft['imgs'] or []
        
        for part in parts:
            match = re.search(r'\[GAMBAR\s*(\d+)\]', part, re.IGNORECASE)
            if match:
                try:
                    idx = int(match.group(1)) - 1
                    if 0 <= idx < len(imgs):
                        st.image(imgs[idx], width=300, caption=f"Img {idx+1}")
                    else:
                        st.caption(f"⚠️ Placeholder [GAMBAR {idx+1}] kosong")
                except: pass
            else:
                if part.strip(): st.markdown(part)
                
        if len(parts) == 1 and imgs:
            st.divider()
            c_ig = st.columns(len(imgs))
            for x, img in enumerate(imgs):
                with c_ig[x]: st.image(img, use_container_width=True)

        st.divider()
        
        # Hidden AI Context
        with st.expander("🔧 (Advanced) Debug AI Context", expanded=False):
            st.info("Ini teks bersih yang dibaca AI (Tag gambar dihapus).")
            cleaned_ans = utils.clean_text_for_embedding(draft['jawab'])
            ctx = database.build_context_text(draft['judul'], cleaned_ans, draft['key'], draft['tag'])
            st.code(ctx, language="text")

# === TAB 3: EDIT/HAPUS ===
with tab3:
    df_e = database.get_all_data_as_df()
    if not df_e.empty:
        opts = [f"{r['ID']} | {r['Judul']}" for _, r in df_e.iterrows()]
        sel = st.selectbox("Pilih Data", opts)
        sel_id = sel.split(" | ")[0]
        row = df_e[df_e['ID'] == sel_id].iloc[0]
        
        with st.form("edit_f"):
            curr = row['Tag']
            idx = list(tags_map.keys()).index(curr) if curr in tags_map else 0
            e_tag = st.selectbox("Modul", list(tags_map.keys()), index=idx)
            e_jud = st.text_input("Judul", value=row['Judul'])
            e_jaw = st.text_area("Jawaban", value=row['Jawaban'])
            e_key = st.text_input("Keyword", value=row['Keyword'])
            e_src = st.text_input("Source", value=row['Source'])
            st.markdown(f"**Img:** `{row['Gambar']}`")
            e_new = st.file_uploader("Overwrite Gambar?", accept_multiple_files=True)
            
            c_up, c_del = st.columns(2)
            if c_up.form_submit_button("Update"):
                p = row['Gambar']
                if e_new: p = utils.save_uploaded_images(e_new, e_jud, e_tag)
                database.upsert_faq(sel_id, e_tag, e_jud, e_jaw, e_key, p, e_src)
                st.toast("Updated!"); time.sleep(1); st.rerun()
            if c_del.form_submit_button("Hapus", type="primary"):
                database.delete_faq(sel_id)
                st.toast("Dihapus"); time.sleep(1); st.rerun()

# === TAB 4: CONFIG ===
with tab4:
    st.header("🎨 Pengaturan Tag")
    flat = [{"Tag":k, "Warna":v.get("color",""), "Desc":v.get("desc","")} 
            for k,v in tags_map.items()]
    st.dataframe(pd.DataFrame(flat), use_container_width=True, hide_index=True)
    st.divider()
    
    with st.form("conf_f", clear_on_submit=True):
        st.subheader("Tambah/Edit Tag")
        n_name = st.text_input("Nama Tag")
        n_col = st.selectbox("Warna Badge", list(utils.COLOR_PALETTE.keys()))
        n_desc = st.text_area("Deskripsi AI")
        
        if st.form_submit_button("Simpan Tag"):
            if n_name:
                hex_c = utils.COLOR_PALETTE[n_col]["hex"]
                tags_map[n_name] = {"color": hex_c, "desc": n_desc}
                utils.save_tags_config(tags_map)
                st.toast("Tag Saved!"); time.sleep(1); st.rerun()
                
    st.divider()
    d_tag = st.selectbox("Hapus Tag", list(tags_map.keys()))
    if st.button("Hapus Tag"):
        del tags_map[d_tag]
        utils.save_tags_config(tags_map)
        st.rerun()