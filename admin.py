import streamlit as st
import pandas as pd
import time
from src import database, utils

# --- AUTH SIMPLE ---
if 'auth' not in st.session_state: st.session_state.auth = False

def login():
    if st.session_state.pass_input == "admin123": # Ganti password
        st.session_state.auth = True
    else:
        st.error("Password salah")

if not st.session_state.auth:
    st.title("🔒 Admin Login")
    st.text_input("Password", type="password", key="pass_input", on_change=login)
    st.stop()

# --- MAIN UI ---
st.title("🛠️ Admin Console")

# Load Tags Mapping
tags_map = utils.load_tags_config()

tab1, tab2, tab3, tab4 = st.tabs(["📊 Data List", "➕ Tambah", "✏️ Edit/Hapus", "⚙️ Config Tags"])

# === TAB 1: LIST ===
with tab1:
    df = database.get_all_data_as_df()
    st.dataframe(df, use_container_width=True, hide_index=True)

# === TAB 2: TAMBAH DATA ===
with tab2:
    col_id, col_modul = st.columns([1, 3])
    with col_id:
        # Auto ID Safe
        coll = database.get_collection()
        next_id = utils.get_next_id_safe(coll)
        st.text_input("ID (Auto)", value=next_id, disabled=True)
    with col_modul:
        i_tag = st.selectbox("Modul", list(tags_map.keys()))
        
    i_judul = st.text_input("Judul Pertanyaan")
    i_jawab = st.text_area("Jawaban", height=150)
    i_key = st.text_input("Keyword Tambahan")
    i_src = st.text_input("Source URL")
    i_imgs = st.file_uploader("Gambar", accept_multiple_files=True)
    
    if st.button("💾 SIMPAN DATA", type="primary"):
        with st.spinner("Menyimpan..."):
            paths = utils.save_uploaded_images(i_imgs, i_judul, i_tag)
            database.upsert_faq(next_id, i_tag, i_judul, i_jawab, i_key, paths, i_src)
            st.toast("Data tersimpan!", icon="✅")
            time.sleep(1)
            st.rerun()

# === TAB 3: EDIT/HAPUS ===
with tab3:
    df = database.get_all_data_as_df()
    if not df.empty:
        opts = [f"{r['ID']} | {r['Judul']}" for _, r in df.iterrows()]
        sel = st.selectbox("Pilih Data", opts)
        sel_id = sel.split(" | ")[0]
        
        # Get Current Data
        row = df[df['ID'] == sel_id].iloc[0]
        
        with st.form("edit_form"):
            e_tag = st.selectbox("Modul", list(tags_map.keys()), index=list(tags_map.keys()).index(row['Tag']) if row['Tag'] in tags_map else 0)
            e_judul = st.text_input("Judul", value=row['Judul'])
            e_jawab = st.text_area("Jawaban", value=row['Jawaban'])
            e_key = st.text_input("Keyword", value=row['Keyword'])
            e_src = st.text_input("URL", value=row['Source'])
            
            st.caption(f"Gambar saat ini: {row['Gambar']}")
            e_imgs = st.file_uploader("Ganti Gambar (Overwrite)", accept_multiple_files=True)
            
            c1, c2 = st.columns(2)
            if c1.form_submit_button("Update"):
                final_path = row['Gambar']
                if e_imgs:
                    final_path = utils.save_uploaded_images(e_imgs, e_judul, e_tag)
                database.upsert_faq(sel_id, e_tag, e_judul, e_jawab, e_key, final_path, e_src)
                st.success("Updated!")
                st.rerun()
                
            if c2.form_submit_button("Hapus Data", type="primary"):
                database.delete_faq(sel_id)
                st.warning("Deleted.")
                st.rerun()

# === TAB 4: CONFIG TAGS ===
with tab4:
    st.header("🎨 Atur Kategori & Warna")
    
    # Editor Table
    current_df = pd.DataFrame(list(tags_map.items()), columns=["Tag", "Hex Color"])
    st.dataframe(current_df, use_container_width=True)
    
    c_new_name = st.text_input("Nama Tag Baru/Edit")
    c_new_col = st.color_picker("Warna Badge")
    
    if st.button("Simpan Tag"):
        tags_map[c_new_name] = c_new_col
        utils.save_tags_config(tags_map)
        st.rerun()
        
    st.divider()
    del_tag = st.selectbox("Hapus Tag", list(tags_map.keys()))
    if st.button("Hapus Tag Terpilih"):
        del tags_map[del_tag]
        utils.save_tags_config(tags_map)
        st.rerun()