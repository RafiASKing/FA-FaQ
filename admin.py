import streamlit as st
import pandas as pd
import time
from src import database, utils

# --- AUTH SIMPLE ---
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

tab1, tab2, tab3, tab4 = st.tabs(["📊 Data List", "➕ Tambah (Auto-Clear)", "✏️ Edit/Hapus", "⚙️ Config Tags"])

# === TAB 1: LIST (FIX WARNING & NEW COLUMNS) ===
with tab1:
    st.caption("Menampilkan database lengkap termasuk 'Hidden Context' yang dibaca AI.")
    df = database.get_all_data_as_df()
    

    # ATAU: Jika versi streamlit kamu minta 'width', gunakan parameter column_config agar rapi
    st.dataframe(
        df, 
        hide_index=True,
        width="stretch"
    )

# === TAB 2: TAMBAH DATA (DENGAN FITUR AUTO-CLEAR) ===
with tab2:
    st.info("Form ini akan otomatis reset setelah tombol Simpan ditekan.")
    
    # Hitung ID di luar form agar user tau ID nya
    coll = database.get_collection()
    next_id = utils.get_next_id_safe(coll)
    st.markdown(f"**Next ID:** `{next_id}`")

    # --- FORM START ---
    # clear_on_submit=True adalah kuncinya!
    with st.form("form_tambah_data", clear_on_submit=True):
        col_modul, col_judul = st.columns([1, 3])
        
        with col_modul:
            i_tag = st.selectbox("Modul", list(tags_map.keys()))
        with col_judul:
            i_judul = st.text_input("Judul Pertanyaan")
            
        i_jawab = st.text_area("Jawaban", height=150)
        i_key = st.text_input("Keyword Tambahan")
        i_src = st.text_input("Source URL")
        i_imgs = st.file_uploader("Gambar", accept_multiple_files=True)
        
        # Tombol Submit ada di dalam Form
        submitted = st.form_submit_button("💾 SIMPAN DATA", type="primary")
        
        if submitted:
            if not i_judul or not i_jawab:
                st.error("Judul dan Jawaban wajib diisi!")
            else:
                try:
                    with st.spinner("Sedang menyimpan & reset form..."):
                        # 1. Hitung ID lagi TEPAT sebelum simpan (Real-time check)
                        real_coll = database.get_collection()
                        safe_id_now = utils.get_next_id_safe(real_coll)
                        
                        # 2. Save Image
                        paths = utils.save_uploaded_images(i_imgs, i_judul, i_tag)
                        
                        # 3. Upsert pakai SAFE ID yang baru
                        database.upsert_faq(safe_id_now, i_tag, i_judul, i_jawab, i_key, paths, i_src)
                        
                        st.toast(f"✅ Data ID {safe_id_now} Tersimpan! Form di-reset.")
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    st.error(f"Gagal menyimpan data: {e}")

# === TAB 3: EDIT/HAPUS ===
with tab3:
    df = database.get_all_data_as_df()
    if not df.empty:
        opts = [f"{r['ID']} | {r['Judul']}" for _, r in df.iterrows()]
        sel = st.selectbox("Pilih Data untuk Edit", opts)
        sel_id = sel.split(" | ")[0]
        
        row = df[df['ID'] == sel_id].iloc[0]
        
        with st.form("edit_form"):
            st.caption(f"Editing ID: {sel_id}")
            
            # Handle Index Error kalau tag lama udah dihapus dari config
            curr_tag = row['Tag']
            idx_tag = 0
            if curr_tag in tags_map:
                idx_tag = list(tags_map.keys()).index(curr_tag)
            
            e_tag = st.selectbox("Modul", list(tags_map.keys()), index=idx_tag)
            e_judul = st.text_input("Judul", value=row['Judul'])
            e_jawab = st.text_area("Jawaban", value=row['Jawaban'])
            e_key = st.text_input("Keyword", value=row['Keyword'])
            e_src = st.text_input("URL", value=row['Source'])
            
            st.markdown(f"**Gambar saat ini:** `{row['Gambar']}`")
            e_imgs = st.file_uploader("Upload Gambar Baru (Akan menimpa gambar lama)", accept_multiple_files=True)
            
            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 Update Perubahan"):
                final_path = row['Gambar']
                if e_imgs:
                    final_path = utils.save_uploaded_images(e_imgs, e_judul, e_tag)
                
                database.upsert_faq(sel_id, e_tag, e_judul, e_jawab, e_key, final_path, e_src)
                st.toast("Update Berhasil!", icon="✅")
                time.sleep(1)
                st.rerun()
                
            if c2.form_submit_button("🗑️ Hapus Data Ini", type="primary"):
                database.delete_faq(sel_id)
                st.toast("Data dihapus.", icon="🗑️")
                time.sleep(1)
                st.rerun()

# === TAB 4: CONFIG TAGS ===
with tab4:
    st.header("🎨 Atur Kategori & Warna")
    current_df = pd.DataFrame(list(tags_map.items()), columns=["Tag", "Hex Color"])
    st.dataframe(current_df, width="stretch") # Sesuaikan warning disini juga
    
    with st.form("tag_form", clear_on_submit=True):
        c_new_name = st.text_input("Nama Tag Baru/Edit")
        c_new_col = st.color_picker("Warna Badge")
        if st.form_submit_button("Simpan Tag"):
            tags_map[c_new_name] = c_new_col
            utils.save_tags_config(tags_map)
            st.rerun()
        
    st.divider()
    del_tag = st.selectbox("Hapus Tag", list(tags_map.keys()))
    if st.button("Hapus Tag Terpilih"):
        del tags_map[del_tag]
        utils.save_tags_config(tags_map)
        st.rerun()