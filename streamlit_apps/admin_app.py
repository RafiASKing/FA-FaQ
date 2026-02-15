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

# --- PAGE CONFIG (Harus paling atas sebelum command Streamlit lainnya) ---
st.set_page_config(page_title="Admin Console", layout="wide")

# Import dari service layer baru
from app.services import FaqService, SearchService
from core.tag_manager import TagManager
from core.image_handler import ImageHandler
from core.content_parser import ContentParser
from core.logger import log_failed_search, clear_failed_search_log, get_search_log_path, clear_search_log
from core.group_config import GroupConfig
from core.bot_config import BotConfig
from config.settings import settings, paths
from config.constants import COLOR_PALETTE


# --- AUTH STATE ---
if 'auth' not in st.session_state:
    st.session_state.auth = False


def login():
    """Handle login authentication."""
    password = st.session_state.pass_input
    target = settings.admin_password_hash

    try:
        # Try bcrypt hash comparison first (production)
        if bcrypt.checkpw(password.encode('utf-8'), target.encode('utf-8')):
            st.session_state.auth = True
            return
    except (ValueError, TypeError):
        # Not a valid bcrypt hash — fall back to plain-text comparison (dev only)
        if password == target:
            st.session_state.auth = True
            return

    st.error("Password salah")


# --- LOGIN SCREEN ---
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center;'>🔒 Admin Login</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.text_input("Password", type="password", key="pass_input", on_change=login)
    st.stop()


# --- MAIN UI ---
st.title("🛠️ Admin Console (Safe Mode)")

tags_map = TagManager.load_tags()

# State Management
if 'preview_mode' not in st.session_state:
    st.session_state.preview_mode = False
if 'draft_data' not in st.session_state:
    st.session_state.draft_data = {}

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Database", "➕ New FaQ", "✏️ Edit/Delete FaQ", "⚙️ Config Tags", "📈 Analytics", "🏢 Group Settings"
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
        except (ValueError, IndexError):
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
                    except Exception:
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
                    with st.spinner("Menyimpan ke Typesense..."):
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
    st.caption("Download seluruh data FAQ dan gambar.")

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
    st.subheader("📈 Analytics Dashboard")
    st.caption("Statistik penggunaan FAQ bot secara keseluruhan.")
    
    search_log_path = get_search_log_path()
    
    if search_log_path.exists():
        df_search = pd.read_csv(search_log_path)
        df_search['timestamp'] = pd.to_datetime(df_search['timestamp'], errors='coerce')
        df_search = df_search.dropna(subset=['timestamp'])
        
        if not df_search.empty:
            now = pd.Timestamp.now()
            today = now.normalize()
            week_ago = today - pd.Timedelta(days=7)
            
            total_queries = len(df_search)
            today_queries = len(df_search[df_search['timestamp'] >= today])
            week_queries = len(df_search[df_search['timestamp'] >= week_ago])
            avg_score = df_search['score'].astype(float).mean()
            avg_response = df_search['response_ms'].astype(float).mean()
            
            # --- KPI Metrics ---
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("📊 Total Queries", f"{total_queries:,}")
            m2.metric("📅 Today", f"{today_queries:,}")
            m3.metric("📆 This Week", f"{week_queries:,}")
            m4.metric("🎯 Avg Score", f"{avg_score:.0f}%")
            m5.metric("⚡ Avg Response", f"{avg_response:.0f}ms")
            
            st.divider()
            
            # --- Charts Row ---
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.markdown("#### 📈 Queries per Day")
                daily = df_search.set_index('timestamp').resample('D').size().reset_index(name='count')
                daily = daily.tail(30)  # Last 30 days
                st.bar_chart(daily.set_index('timestamp')['count'])
            
            with chart_col2:
                st.markdown("#### 🎯 Score Distribution")
                df_scored = df_search[df_search['score'].astype(float) > 0]
                if not df_scored.empty:
                    bins = [0, 50, 70, 75, 85, 100]
                    labels = ['0-50%', '50-70%', '70-75%', '75-85%', '85-100%']
                    df_scored = df_scored.copy()
                    df_scored['bucket'] = pd.cut(df_scored['score'].astype(float), bins=bins, labels=labels, include_lowest=True)
                    dist = df_scored['bucket'].value_counts().sort_index()
                    st.bar_chart(dist)
                else:
                    st.info("No scored queries yet.")
            
            st.divider()
            
            # --- Top FAQs & Mode Split ---
            faq_col, mode_col = st.columns(2)
            
            with faq_col:
                st.markdown("#### 🏆 Top 10 FAQs")
                top_faqs = df_search[df_search['faq_title'].astype(str) != ''].groupby('faq_title').size().sort_values(ascending=False).head(10)
                if not top_faqs.empty:
                    st.dataframe(
                        top_faqs.reset_index().rename(columns={'faq_title': 'FAQ', 0: 'Hits'}),
                        use_container_width=True, hide_index=True
                    )
                else:
                    st.info("No FAQ hits yet.")
            
            with mode_col:
                st.markdown("#### 🔄 Mode Split")
                mode_counts = df_search['mode'].value_counts()
                st.dataframe(
                    mode_counts.reset_index().rename(columns={'mode': 'Mode', 'count': 'Queries'}),
                    use_container_width=True, hide_index=True
                )
                
                st.markdown("#### 📡 Source Split")
                src_counts = df_search['source'].value_counts()
                st.dataframe(
                    src_counts.reset_index().rename(columns={'source': 'Source', 'count': 'Queries'}),
                    use_container_width=True, hide_index=True
                )
            
            st.divider()
            
            # --- Recent Queries ---
            st.markdown("#### 🕐 Recent Queries (last 50)")
            recent = df_search.sort_values('timestamp', ascending=False).head(50)
            display_cols = ['timestamp', 'query', 'score', 'faq_title', 'mode', 'response_ms']
            st.dataframe(
                recent[display_cols].rename(columns={
                    'timestamp': 'Time', 'query': 'Query', 'score': 'Score',
                    'faq_title': 'FAQ', 'mode': 'Mode', 'response_ms': 'ms'
                }),
                use_container_width=True, hide_index=True
            )
            
            st.divider()
            
            # --- Clear Log ---
            if st.button("🗑️ Clear Search Log", key="clear_search_log"):
                clear_search_log()
                st.toast("Search log cleared.", icon="🗑️")
                time.sleep(0.5)
                st.rerun()
        else:
            st.info("Search log exists but has no valid data yet.")
    else:
        st.info("📊 No search data yet. Data will appear after users start querying the bot.")
    
    st.divider()
    
    # --- Failed Searches (original section) ---
    st.subheader("❌ Failed Searches")
    st.caption("Queries that returned no relevant result.")
    
    log_file = paths.FAILED_SEARCH_LOG
    
    if log_file.exists():
        df_log = pd.read_csv(log_file)
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.metric("Total Misses", len(df_log))
        with col2:
            if st.button("🗑️ Clear Failed Log"):
                clear_failed_search_log()
                st.rerun()
        
        if not df_log.empty:
            # Support both old ("Timestamp") and new ("timestamp") header formats
            ts_col = "timestamp" if "timestamp" in df_log.columns else "Timestamp"
            df_log = df_log.sort_values(by=ts_col, ascending=False)
            st.dataframe(df_log, use_container_width=True, hide_index=True)
    else:
        st.info("No failed searches recorded. System is working well!")


# === TAB 6: GROUP SETTINGS ===
with tab6:
    st.subheader("🏢 Pengaturan Grup WhatsApp")
    st.caption("Atur modul yang diizinkan untuk setiap grup. Grup otomatis terdaftar saat pertama kali mention @faq.")
    
    groups = GroupConfig.get_all_groups()
    available_modules = ["all"] + list(tags_map.keys())
    
    if not groups:
        st.info("Belum ada grup terdaftar. Grup akan otomatis muncul setelah mention @faq pertama.")
    else:
        # Sort groups by first_seen descending
        sorted_groups = sorted(
            groups.items(), 
            key=lambda x: x[1].get('first_seen', ''), 
            reverse=True
        )
        
        for group_id, config in sorted_groups:
            with st.container(border=True):
                col_name, col_modules = st.columns([2, 3])
                
                with col_name:
                    st.markdown(f"**{config.get('name', 'Unknown Group')}**")
                    st.caption(f"`{group_id[:30]}...`")
                    st.caption(f"📅 First seen: {config.get('first_seen', 'N/A')[:10]}")
                
                with col_modules:
                    current_modules = config.get('allowed_modules', ['all'])
                    
                    # Multiselect for allowed modules
                    new_modules = st.multiselect(
                        "Allowed Modules",
                        options=available_modules,
                        default=current_modules,
                        key=f"modules_{group_id}",
                        label_visibility="collapsed"
                    )
                    
                    # Save button
                    if st.button("💾 Save", key=f"save_{group_id}", use_container_width=True):
                        if not new_modules:
                            new_modules = ["all"]  # Default to all if empty
                        GroupConfig.set_allowed_modules(group_id, new_modules)
                        st.toast(f"✅ Saved: {config.get('name')}", icon="✅")
                        time.sleep(0.5)
                        st.rerun()
        
        st.divider()
        
        # Danger Zone: Delete Group
        with st.expander("🗑️ Hapus Grup dari Daftar", expanded=False):
            st.warning("⚠️ Menghapus grup akan menghilangkan konfigurasi. Grup akan kembali terdaftar (default: all modules) saat mention @faq lagi.")
            
            del_group = st.selectbox(
                "Pilih Grup",
                options=list(groups.keys()),
                format_func=lambda x: groups[x].get('name', x)
            )
            
            if st.button("🔥 Hapus Grup Ini", type="primary"):
                GroupConfig.delete_group(del_group)
                st.toast("Grup telah dihapus.", icon="🗑️")
                time.sleep(1)
                st.rerun()
    
    st.divider()
    
    # === BOT SETTINGS ===
    st.subheader("🤖 Bot Settings")
    
    current_mode = BotConfig.get_search_mode()
    
    col_mode, col_info = st.columns([1, 2])
    
    with col_mode:
        mode_options = {
            "immediate": "⚡ Immediate (Top 1)",
            "agent": "🧠 Agent Flash",
            "agent_pro": "🧠💎 Agent Pro (Deeper)"
        }
        mode_keys = list(mode_options.keys())

        selected_mode = st.radio(
            "Search Mode",
            options=mode_keys,
            format_func=lambda x: mode_options[x],
            index=mode_keys.index(current_mode) if current_mode in mode_keys else 0,
            key="search_mode_radio"
        )
        
        if selected_mode != current_mode:
            if st.button("💾 Save Mode", use_container_width=True):
                BotConfig.set_search_mode(selected_mode)
                st.toast(f"✅ Search mode changed to: {mode_options[selected_mode]}", icon="🤖")
                time.sleep(0.5)
                st.rerun()
    
    with col_info:
        if current_mode == "immediate":
            st.info("""
            **⚡ Immediate Mode**
            - Returns top 1 result with 70% relevancy threshold
            - Fastest response (~200ms)
            - Good for most use cases
            """)
        elif current_mode == "agent_pro":
            st.warning("""
            **🧠💎 Agent Pro Mode**
            - Uses Gemini Pro for deeper analysis
            - Most accurate for complex/ambiguous questions
            - Slower (~5-10s), higher API cost
            """)
        else:
            st.success("""
            **🧠 Agent Flash Mode**
            - LLM grades top 20 candidates
            - Better accuracy for complex questions
            - Moderate speed (~2-3s)
            """)
            
            # Confidence threshold slider
            threshold = BotConfig.get_confidence_threshold()
            new_threshold = st.slider(
                "Confidence Threshold",
                min_value=0.0,
                max_value=1.0,
                value=threshold,
                step=0.1,
                help="Minimum confidence for LLM to accept a match"
            )
            
            if new_threshold != threshold:
                if st.button("💾 Save Threshold", key="save_threshold"):
                    BotConfig.set_confidence_threshold(new_threshold)
                    st.toast(f"✅ Threshold set to {new_threshold}", icon="⚙️")
