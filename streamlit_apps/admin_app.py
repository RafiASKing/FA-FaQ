"""
Admin App - Streamlit application untuk mengelola FAQ.
Migrasi dari admin.py original dengan menggunakan service layer baru.
"""

import streamlit as st
import pandas as pd
import time
import re
import os
import shutil
import bcrypt

# Import dari service layer baru
from app.services import FaqService, SearchService
from core.tag_manager import TagManager
from core.image_handler import ImageHandler
from core.content_parser import ContentParser
from core.logger import log_failed_search, clear_failed_search_log
from config.settings import settings, paths
from config.constants import COLOR_PALETTE


# --- AUTH STATE ---
if 'auth' not in st.session_state:
    st.session_state.auth = False


def login():
    """Handle login authentication."""
    input_bytes = st.session_state.pass_input.encode('utf-8')
    target_hash = settings.admin_password_hash.encode('utf-8')
    
    if bcrypt.checkpw(input_bytes, target_hash):
        st.session_state.auth = True
    else:
        st.error("Password salah")


# --- LOGIN SCREEN ---
if not st.session_state.auth:
    st.set_page_config(page_title="Admin Login")
    st.markdown("<h1 style='text-align: center;'>🔒 Admin Login</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.text_input("Password", type="password", key="pass_input", on_change=login)
    st.stop()


# --- MAIN UI SETUP ---
st.set_page_config(page_title="Admin Console", layout="wide")
st.title("🛠️ Admin Console (Safe Mode)")

tags_map = TagManager.load_tags()

# State Management
if 'preview_mode' not in st.session_state:
    st.session_state.preview_mode = False
if 'draft_data' not in st.session_state:
    st.session_state.draft_data = {}

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Database", "➕ New FaQ", "✏️ Edit/Delete FaQ", "⚙️ Config Tags", "📈 Analytics"
])


# === TAB 1: LIST DATA ===
with tab1:
    if st.button("🔄 Refresh Data"):
        st.rerun()
    
    df = FaqService.get_all_as_dataframe()
    st.dataframe(df, use_container_width=True, hide_index=True)


# === TAB 2: TAMBAH DATA (SMART EDITOR) ===
with tab2:
    # --- SMART CALLBACKS ---
    def add_text(text):
        """Menambahkan teks ke akhir editor."""
        if 'in_a' in st.session_state:
            st.session_state.in_a += text

    def add_next_image_tag():
        """Auto increment tag [GAMBAR X]."""
        current_text = st.session_state.get('in_a', "")
        next_num = ContentParser.count_image_tags(current_text) + 1
        tag_to_insert = f"\n[GAMBAR {next_num}]\n"
        st.session_state.in_a += tag_to_insert

    # --- PHASE 1: INPUT FORM ---
    if not st.session_state.preview_mode:
        # Load Draft
        default_tag = st.session_state.draft_data.get('tag', list(tags_map.keys())[0])
        default_judul = st.session_state.draft_data.get('judul', '')
        default_jawab = st.session_state.draft_data.get('jawab', '')
        default_key = st.session_state.draft_data.get('key', '')
        default_src = st.session_state.draft_data.get('src', '')
        
        try:
            idx_tag = list(tags_map.keys()).index(default_tag)
        except:
            idx_tag = 0

        st.subheader("📝 FaQ/SOP Baru")
        
        # Row 1: Module & Judul
        col_m, col_j = st.columns([1, 3])
        with col_m:
            i_tag = st.selectbox("Modul", list(tags_map.keys()), index=idx_tag, key="in_t")
        with col_j:
            i_judul = st.text_input("Judul Masalah (Pertanyaan/SOP)", value=default_judul, key="in_j")
        
        # Row 2: Smart Toolbar & Editor
        st.markdown("**Jawaban / Solusi:**")
        
        tb1, tb2, tb3, tb_spacer = st.columns([1, 1, 2, 4])
        
        tb1.button("𝗕 Bold", on_click=add_text, args=(" **teks tebal** ",),
                   help="Tebalkan teks", use_container_width=True)
        
        tb2.button("Bars", on_click=add_text, args=("\n- Langkah 1\n- Langkah 2",),
                   help="Buat List", use_container_width=True)
        
        tb3.button("+ Klik ini untuk add penanda gambar", on_click=add_next_image_tag,
                   type="primary", icon="🖼️", use_container_width=True,
                   help="Otomatis memasukkan tag [GAMBAR 1], [GAMBAR 2], dst.")

        # Text Area
        i_jawab = st.text_area("Editor", value=default_jawab, height=300, key="in_a", label_visibility="collapsed")
        st.caption("💡 *Tips: Klik tombol '📸' untuk memasukkan placeholder gambar secara urut.*")
        
        # Row 3: Meta Info & Upload
        c_k, c_s = st.columns(2)
        with c_k:
            st.markdown("Term terkait / Bahasa User (HyDE) 👇")
            i_key = st.text_input("Hidden Label", value=default_key, key="in_k",
                                  placeholder="Contoh: Gabisa login, User not found, Kok gagal discharge?...",
                                  label_visibility="collapsed",
                                  help="Masukkan kata-kata yang mungkin diketik user saat panik.")
        
        with c_s:
            st.markdown("Sumber Info/Source URL")
            i_src = st.text_input("Hidden Label 2", value=default_src, key="in_s", label_visibility="collapsed")
        
        i_imgs = st.file_uploader("Upload Gambar", accept_multiple_files=True, key="in_i")
        
        st.divider()
        if st.button("🔍 Lanjut ke Preview", type="primary", use_container_width=True):
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
        
        st.info("📱 **Mode Preview:** Periksa tampilan sebelum Publish.")
        
        with st.container(border=True):
            hex_color = tags_map.get(draft['tag'], {}).get("color", "#808080")
            st.markdown(f"### <span style='color:{hex_color}'>[{draft['tag']}]</span> {draft['judul']}", unsafe_allow_html=True)
            st.caption(f"🔑 Keywords/HyDE: {draft['key']}")
            st.divider()
            
            # Render Preview
            parts = re.split(r'(\[GAMBAR\s*\d+\])', draft['jawab'], flags=re.IGNORECASE)
            imgs = draft['imgs'] or []
            
            for part in parts:
                match = re.search(r'\[GAMBAR\s*(\d+)\]', part, re.IGNORECASE)
                if match:
                    try:
                        idx = int(match.group(1)) - 1
                        if 0 <= idx < len(imgs):
                            st.image(imgs[idx], width=400, caption=f"Gambar {idx+1}")
                        else:
                            st.warning(f"⚠️ [GAMBAR {idx+1}] ditulis tapi file belum diupload.")
                    except:
                        pass
                else:
                    if part.strip():
                        st.markdown(part)
        
        st.divider()
        c_back, c_save = st.columns([1, 3])
        
        with c_back:
            if st.button("⬅️ Edit Lagi", use_container_width=True):
                st.session_state.preview_mode = False
                st.rerun()
        
        with c_save:
            if st.button("💾 PUBLISH KE DATABASE", type="primary", use_container_width=True):
                try:
                    with st.spinner("Menyimpan ke ChromaDB..."):
                        # Simpan Gambar
                        img_paths = ImageHandler.save_uploaded_images(
                            draft['imgs'], draft['judul'], draft['tag']
                        )
                        
                        # Upsert ke DB
                        new_id = FaqService.upsert(
                            tag=draft['tag'],
                            judul=draft['judul'],
                            jawaban=draft['jawab'],
                            keywords=draft['key'],
                            img_paths=img_paths,
                            source_url=draft['src']
                        )
                        
                        st.balloons()
                        st.success(f"✅ Data Tersimpan! ID Dokumen: {new_id}")
                        
                        # Reset
                        st.session_state.preview_mode = False
                        st.session_state.draft_data = {}
                        time.sleep(2)
                        st.rerun()
                except Exception as e:
                    st.error(f"Error Save: {e}")


# === TAB 3: EDIT/HAPUS ===
with tab3:
    st.header("✏️ Edit Data Lama")
    df_e = FaqService.get_all_as_dataframe()
    
    if not df_e.empty:
        opts = [f"{r['ID']} | {r['Judul']}" for _, r in df_e.iterrows()]
        sel = st.selectbox("Pilih Data", opts)
        
        if sel:
            sel_id = sel.split(" | ")[0]
            row = df_e[df_e['ID'] == sel_id].iloc[0]
            
            with st.form("edit_form"):
                curr = row['Tag']
                idx = list(tags_map.keys()).index(curr) if curr in tags_map else 0
                
                c_id, c_t = st.columns([1, 4])
                with c_id:
                    st.text_input("ID", value=sel_id, disabled=True)
                with c_t:
                    e_tag = st.selectbox("Modul", list(tags_map.keys()), index=idx)
                
                e_jud = st.text_input("Judul SOP", value=row['Judul'])
                e_jaw = st.text_area("Jawaban (Gunakan [GAMBAR X])", value=row['Jawaban'], height=200)
                e_key = st.text_input("Keyword / Bahasa User (HyDE)", value=row['Keyword'],
                                      help="Isi dengan variasi pertanyaan user.")
                e_src = st.text_input("Source URL", value=row['Source'])
                
                st.markdown(f"**Path Gambar Saat Ini:** `{row['Gambar']}`")
                e_new = st.file_uploader("Timpa Gambar Baru (Opsional)", accept_multiple_files=True)
                
                st.divider()
                
                c_up, c_space, c_del = st.columns([4, 0.5, 2])
                
                with c_up:
                    is_update = st.form_submit_button("💾 UPDATE DATA", type="primary", use_container_width=True)
                
                with c_del:
                    is_delete = st.form_submit_button("🗑️ Hapus Permanen", type="secondary", use_container_width=True)
                
                if is_update:
                    p = row['Gambar']
                    if e_new:
                        p = ImageHandler.save_uploaded_images(e_new, e_jud, e_tag)
                    
                    FaqService.upsert(
                        tag=e_tag,
                        judul=e_jud,
                        jawaban=e_jaw,
                        keywords=e_key,
                        img_paths=p,
                        source_url=e_src,
                        doc_id=sel_id
                    )
                    st.toast("Data Berhasil Diupdate!", icon="✅")
                    time.sleep(1)
                    st.rerun()
                
                if is_delete:
                    FaqService.delete(sel_id)
                    st.toast("Data & Gambar Telah Dihapus.", icon="🗑️")
                    time.sleep(1)
                    st.rerun()


# === TAB 4: CONFIG ===
with tab4:
    st.subheader("⚙️ Konfigurasi Tag")
    
    # Tampilkan Tabel Config
    flat = [{"Tag": k, "Warna": v.get("color", ""), "Sinonim": v.get("desc", "")} for k, v in tags_map.items()]
    st.dataframe(pd.DataFrame(flat), use_container_width=True, hide_index=True)
    
    st.divider()

    # Tambah / Edit Tag
    with st.expander("➕ Tambah / Update Tag", expanded=True):
        with st.form("conf_f", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                n_name = st.text_input("Nama Tag (ex: ED)", help="Jika nama sama, akan mengupdate.")
            with c2:
                n_col = st.selectbox("Warna Badge", list(COLOR_PALETTE.keys()))
            n_desc = st.text_input("Sinonim / Kepanjangan", placeholder="ex: Emergency, Poli, Medical Record")
            
            if st.form_submit_button("Simpan Konfigurasi"):
                if n_name:
                    hex_c = COLOR_PALETTE[n_col]["hex"]
                    TagManager.add_tag(n_name, hex_c, n_desc)
                    st.toast(f"Tag '{n_name}' berhasil disimpan!", icon="✅")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Nama Tag wajib diisi.")

    # Hapus Tag
    with st.expander("🗑️ Hapus Tag", expanded=False):
        st.markdown("### Hapus Tag dari Sistem")
        
        del_tag = st.selectbox("Pilih Tag untuk dihapus", list(tags_map.keys()), key="del_tag_sel")
        
        # Safety Check
        count_usage = FaqService.count_by_tag(del_tag)
        
        if count_usage > 0:
            st.error(f"⚠️ **PERINGATAN:** Tag `{del_tag}` digunakan oleh **{count_usage} Dokumen** FaQ!")
            st.markdown("""
            **Saran:** Edit dokumen tersebut dulu dan ganti tag-nya sebelum menghapus.
            """)
        else:
            st.success(f"✅ Aman: Tidak ada dokumen yang menggunakan tag `{del_tag}`.")

        c_del_warn, c_del_btn = st.columns([3, 1])
        with c_del_btn:
            if st.button("🔥 Hapus Tag Ini", type="primary", use_container_width=True):
                TagManager.delete_tag(del_tag)
                st.toast(f"Tag '{del_tag}' telah dihapus.", icon="🗑️")
                time.sleep(1)
                st.rerun()

    st.divider()
    st.subheader("💾 Backup & Restore")
    st.caption("Download seluruh data ChromaDB dan gambar.")

    if st.button("📦 Download Full Backup", key="backup_btn"):
        with st.spinner("Mempersiapkan arsip backup..."):
            temp_dir = paths.BASE_DIR / "tmp_backup_bundle"
            archive_base = paths.BASE_DIR / f"backup_faq_{int(time.time())}"
            archive_file = ""
            backup_bytes = None
            
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                os.makedirs(temp_dir, exist_ok=True)

                copied_any = False
                for folder_name in ["data", "images"]:
                    src_path = paths.BASE_DIR / folder_name
                    dst_path = temp_dir / folder_name
                    if src_path.exists():
                        shutil.copytree(src_path, dst_path)
                        copied_any = True

                if not copied_any:
                    st.warning("Folder data/images tidak ditemukan.")
                else:
                    archive_file = shutil.make_archive(str(archive_base), 'zip', temp_dir)
                    with open(archive_file, "rb") as f:
                        backup_bytes = f.read()
            except Exception as e:
                st.error(f"Gagal membuat backup: {e}")
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
                if archive_file and os.path.exists(archive_file):
                    os.remove(archive_file)

        if backup_bytes:
            st.download_button(
                label="⬇️ Klik untuk Simpan ZIP",
                data=backup_bytes,
                file_name=f"backup_faq_{int(time.time())}.zip",
                mime="application/zip"
            )


# === TAB 5: ANALYTICS ===
with tab5:
    st.subheader("📈 Pencarian Gagal (User Feedback)")
    st.caption("Daftar kata kunci yang dicari User tapi hasilnya tidak relevan.")
    
    log_file = paths.FAILED_SEARCH_LOG
    
    if log_file.exists():
        df_log = pd.read_csv(log_file)
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.metric("Total Miss", len(df_log))
        with col2:
            if st.button("🗑️ Clear Log"):
                clear_failed_search_log()
                st.rerun()
        
        if not df_log.empty:
            df_log = df_log.sort_values(by="Timestamp", ascending=False)
            st.dataframe(df_log, use_container_width=True)
    else:
        st.info("Belum ada data pencarian gagal. Sistem bekerja dengan baik!")
