import streamlit as st
import os
import math
import re
from src import database, utils

# --- PAGE CONFIG ---
st.set_page_config(page_title="Knowledge Base AI", page_icon="🧠", layout="centered")

# --- CSS CUSTOMIZATION ---
st.markdown("""
<style>
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        margin-bottom: 8px;
        background-color: white;
    }
    .stExpander p {
        font-size: 16px;
        font-weight: 500;
    }
    a { text-decoration: none; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- HELPER: WARNA BADGE ---
def get_badge_syntax(tag_name):
    tags_cfg = utils.load_tags_config()
    tag_data = tags_cfg.get(tag_name, {})
    
    if isinstance(tag_data, dict):
        hex_color = tag_data.get("color", "#808080")
    else:
        hex_color = str(tag_data) 

    st_color_name = "gray"
    for label, palette_data in utils.COLOR_PALETTE.items():
        if palette_data["hex"].lower() == hex_color.lower():
            st_color_name = palette_data["name"]
            break
            
    return f":{st_color_name}-background[{tag_name}]"

# --- HELPER: RENDER INLINE IMAGE ---
def render_answer_with_mixed_content(jawaban_text, images_str):
    """
    Render teks yang mendukung marker [GAMBAR X].
    Jika tidak ada marker, gambar muncul di bawah.
    """
    if not images_str or str(images_str).lower() == 'none':
        st.markdown(jawaban_text)
        return

    img_list = images_str.split(';')
    
    # Regex untuk menangkap [GAMBAR X] (Case Insensitive)
    pattern = r'(\[GAMBAR\s*\d+\])'
    parts = re.split(pattern, jawaban_text, flags=re.IGNORECASE)
    
    # Fallback: Jika tidak ada marker sama sekali
    if len(parts) == 1:
        st.markdown(jawaban_text)
        if len(img_list) > 0:
            st.markdown("---")
            for img_path in img_list:
                real_path = utils.fix_image_path_for_ui(img_path)
                if real_path and os.path.exists(real_path):
                    st.image(real_path, use_container_width=True)
        return

    # Hybrid Render
    for part in parts:
        match = re.search(r'\[GAMBAR\s*(\d+)\]', part, re.IGNORECASE)
        if match:
            try:
                idx = int(match.group(1)) - 1
                if 0 <= idx < len(img_list):
                    real_path = utils.fix_image_path_for_ui(img_list[idx])
                    if real_path and os.path.exists(real_path):
                        st.image(real_path, use_container_width=True)
                else:
                    st.caption(f"⚠️ *Gambar #{idx+1} tidak ditemukan (Cek urutan upload)*")
            except ValueError:
                pass
        else:
            if part.strip():
                st.markdown(part)

# --- STATE MANAGEMENT ---
if 'page' not in st.session_state: st.session_state.page = 0
if 'last_query' not in st.session_state: st.session_state.last_query = ""
if 'last_filter' not in st.session_state: st.session_state.last_filter = ""

# --- LOAD FILTER DATA ---
try: db_tags = database.get_unique_tags_from_db()
except: db_tags = []
all_tags = ["Semua Modul"] + (db_tags if db_tags else ["Umum"])

# --- HEADER UI ---
st.title("🧠 Knowledge Base AI")

col_s, col_f = st.columns([3, 1])
with col_s:
    query = st.text_input("Cari Kendala...", placeholder="Contoh: Cara retur obat, Error 505...")
with col_f:
    selected_tag = st.selectbox("Filter", all_tags)

st.divider()

# Reset page jika input berubah
if query != st.session_state.last_query or selected_tag != st.session_state.last_filter:
    st.session_state.page = 0
    st.session_state.last_query = query
    st.session_state.last_filter = selected_tag

# --- FETCH DATA ENGINE ---
all_results = []
is_search_mode = False

if query:
    # MODE 1: SEARCH
    is_search_mode = True
    raw_res = database.search_faq(query, selected_tag, n_results=50)
    
    if raw_res['ids'][0]:
        for i in range(len(raw_res['ids'][0])):
            item = raw_res['metadatas'][0][i]
            # Calculate Confidence Score
            dist = raw_res['distances'][0][i]
            score_pct = max(0, (1 - dist) * 100) 
            item['score'] = score_pct 
            all_results.append(item)
else:
    # MODE 2: BROWSE
    raw_all = database.get_all_faqs_sorted()
    if selected_tag != "Semua Modul":
        all_results = [x for x in raw_all if x['tag'] == selected_tag]
    else:
        all_results = raw_all
    
    for item in all_results: item['score'] = None

# --- PAGINATION ---
ITEMS_PER_PAGE = 10
total_items = len(all_results)
total_pages = math.ceil(total_items / ITEMS_PER_PAGE)

if total_pages > 0 and st.session_state.page >= total_pages: 
    st.session_state.page = 0 

start_idx = st.session_state.page * ITEMS_PER_PAGE
end_idx = start_idx + ITEMS_PER_PAGE
current_page_data = all_results[start_idx:end_idx]

# --- DISPLAY LOOP ---
if not current_page_data:
    if is_search_mode:
        st.warning(f"❌ Tidak ditemukan hasil untuk '{query}' di kategori {selected_tag}.")
    else:
        st.info("📭 Database kosong. Silakan input data di Admin Console.")
else:
    st.caption(f"Menampilkan **{start_idx + 1}-{min(end_idx, total_items)}** dari total **{total_items}** data.")

    for item in current_page_data:
        badge = get_badge_syntax(item.get('tag', 'Umum'))
        judul = item.get('judul', '(Tanpa Judul)')
        
        # Score Display
        score_display = ""
        if item.get('score') is not None:
            val = item['score']
            if val >= 85: sc_color = "green"
            elif val >= 70: sc_color = "orange"
            else: sc_color = "red"
            score_display = f" :{sc_color}[({val:.0f}% Match)]"

        header_text = f"{badge} **{judul}**{score_display}"
        
        with st.expander(label=header_text, expanded=False):
            # Render Jawaban dengan Inline Image support
            render_answer_with_mixed_content(
                item.get('jawaban_tampil', '-'),
                item.get('path_gambar', 'none')
            )
            
            # Source Link
            src_url = item.get('sumber_url', '')
            if src_url and len(str(src_url)) > 3:
                st.markdown(f"<br>🔗 [Buka Referensi Asli]({src_url})", unsafe_allow_html=True)

    # --- NAV BUTTONS ---
    if total_pages > 1:
        st.markdown("---")
        c_p, c_i, c_n = st.columns([1, 2, 1])
        
        with c_p:
            if st.session_state.page > 0:
                if st.button("⬅️ Sebelumnya", use_container_width=True):
                    st.session_state.page -= 1
                    st.rerun()
        with c_i:
            st.markdown(
                f"<div style='text-align:center;color:grey;padding-top:5px;'>"
                f"Hal <b>{st.session_state.page + 1}</b> / {total_pages}</div>", 
                unsafe_allow_html=True
            )
        with c_n:
            if st.session_state.page < total_pages - 1:
                if st.button("Berikutnya ➡️", use_container_width=True):
                    st.session_state.page += 1
                    st.rerun()