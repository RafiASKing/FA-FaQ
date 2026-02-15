"""
User App - Streamlit application untuk pencarian FAQ.
Migrasi dari app.py original dengan menggunakan service layer baru.
"""

import streamlit as st
import os
import math
import warnings

# Import dari service layer baru
from app.services import SearchService
from core.tag_manager import TagManager
from core.content_parser import ContentParser
from core.image_handler import ImageHandler
from core.logger import log_failed_search
from config.constants import (
    ITEMS_PER_PAGE, 
    WEB_TOP_RESULTS,
    RELEVANCE_THRESHOLD,
    HIGH_RELEVANCE_THRESHOLD,
    MEDIUM_RELEVANCE_THRESHOLD,
    HEX_TO_STREAMLIT_COLOR
)
from config.settings import settings


# --- 1. CONFIG & SUPPRESS WARNINGS ---
st.set_page_config(page_title="Hospital Knowledge Base", page_icon="🏥", layout="centered")
warnings.filterwarnings("ignore")

# Load Konfigurasi Tag
TAGS_MAP = TagManager.load_tags()

# CSS Styling
st.markdown("""
<style>
    div[data-testid="stExpander"] {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        background-color: white;
        margin-bottom: 10px;
    }
    div[data-testid="stExpander"] p {
        font-size: 15px;
        font-family: sans-serif;
    }
    .stApp {
        background-color: #FAFAFA;
    }
</style>
""", unsafe_allow_html=True)


# --- 2. HELPER FUNCTIONS ---

def get_badge_color_name(tag: str) -> str:
    """
    Menerjemahkan HEX Code ke Nama Warna Streamlit.
    """
    return TagManager.get_streamlit_color_name(tag)


def render_image_safe(image_path: str):
    """Render gambar dengan pengecekan keberadaan file."""
    if image_path and os.path.exists(image_path):
        st.image(image_path, use_container_width=True)


def render_mixed_content(jawaban_text: str, images_str: str):
    """
    Render konten dengan gambar inline.
    Menggunakan ContentParser untuk parsing.
    """
    parts = ContentParser.get_streamlit_parts(jawaban_text, images_str)
    
    # Check jika hanya ada 1 part text (tidak ada tag [GAMBAR])
    if len(parts) == 1 and parts[0].get('type') == 'text':
        st.markdown(parts[0]['content'])
        
        # Fallback: tampilkan gambar di bawah jika ada
        img_list = ContentParser.parse_image_paths(images_str)
        if img_list:
            st.markdown("---")
            cols = st.columns(min(3, len(img_list)))
            for idx, p in enumerate(img_list):
                clean_p = ImageHandler.fix_path_for_ui(p)
                if clean_p and os.path.exists(clean_p):
                    with cols[idx % 3]:
                        st.image(clean_p, use_container_width=True)
        return
    
    # Render parts
    for part in parts:
        ptype = part.get('type')
        
        if ptype == 'text':
            if part.get('content', '').strip():
                st.markdown(part['content'])
        
        elif ptype == 'image':
            if part.get('exists'):
                render_image_safe(part['path'])
            else:
                st.error(f"🖼️ File gambar tidak ditemukan: {part.get('path')}")
        
        elif ptype == 'missing_image':
            st.caption(f"*(Gambar #{part.get('index')} tidak tersedia)*")
        
        elif ptype == 'divider':
            st.markdown("---")
        
        elif ptype == 'gallery_image':
            if part.get('exists'):
                st.image(part['path'], use_container_width=True)


# --- 3. STATE MANAGEMENT ---
if 'page' not in st.session_state: 
    st.session_state.page = 0
if 'last_query' not in st.session_state: 
    st.session_state.last_query = ""
if 'last_filter' not in st.session_state: 
    st.session_state.last_filter = ""


# --- 4. HEADER UI ---
st.title("⚡Fast Cognitive Search System")
st.caption("Smart Knowledge Base Retrieval")

col_q, col_f = st.columns([3, 1])
with col_q:
    query = st.text_input(
        "Cari isu/kendala:", 
        placeholder="Ketik masalah (cth: Kenapa Gagal Retur Obat, gagal discharge)..."
    )
with col_f:
    # Ambil tag unik dari DB
    try:
        db_tags = SearchService.get_unique_tags()
    except Exception:
        db_tags = []
    all_tags = ["Semua Modul"] + (db_tags if db_tags else [])
    filter_tag = st.selectbox("Filter:", all_tags)


# --- 5. LOGIC PENCARIAN ---
if query != st.session_state.last_query or filter_tag != st.session_state.last_filter:
    st.session_state.page = 0
    st.session_state.last_query = query
    st.session_state.last_filter = filter_tag

results = []
is_search_mode = False

if query:
    is_search_mode = True
    
    # Gunakan SearchService
    tag_filter = filter_tag if filter_tag != "Semua Modul" else None
    search_results = SearchService.search_for_web(query, tag_filter, WEB_TOP_RESULTS)
    
    for r in search_results:
        results.append({
            'id': r.id,
            'tag': r.tag,
            'judul': r.judul,
            'jawaban_tampil': r.jawaban_tampil,
            'path_gambar': r.path_gambar,
            'sumber_url': r.sumber_url,
            'score': r.score,
            'badge_color': r.badge_color
        })
else:
    # Browse mode
    tag_filter = filter_tag if filter_tag != "Semua Modul" else None
    raw_all = SearchService.get_all_faqs(tag_filter)
    
    for item in raw_all:
        results.append({
            'id': item.get('id', ''),
            'tag': item.get('tag', 'Umum'),
            'judul': item.get('judul', ''),
            'jawaban_tampil': item.get('jawaban_tampil', ''),
            'path_gambar': item.get('path_gambar', 'none'),
            'sumber_url': item.get('sumber_url', ''),
            'score': None,
            'badge_color': item.get('badge_color', '#808080')
        })


# --- 6. PAGINATION & DISPLAY ---
total_docs = len(results)
total_pages = math.ceil(total_docs / ITEMS_PER_PAGE) if total_docs > 0 else 1

if st.session_state.page >= total_pages and total_pages > 0:
    st.session_state.page = 0

start_idx = st.session_state.page * ITEMS_PER_PAGE
end_idx = start_idx + ITEMS_PER_PAGE
page_data = results[start_idx:end_idx]

st.divider()

if not page_data:
    if is_search_mode:
        # Catat query gagal
        try:
            log_failed_search(query)
        except Exception:
            pass
        
        # === CALL TO ACTION ===
        st.warning(f"❌ Tidak ditemukan hasil yang relevan (Relevansi < {RELEVANCE_THRESHOLD}%).")
        
        st.markdown("""
        ### 🧐 Belum ada solusinya?
        Sistem telah mencatat pencarianmu untuk perbaikan. Sementara itu, kamu bisa:
        
        1. Coba gunakan kata kunci yang lebih umum.
        2. Atau langsung request bantuan ke Tim IT Support:
        """)
        
        wa_number = settings.wa_support_number
        wa_text = f"Halo Admin, saya cari solusi tentang '{query}' tapi tidak ketemu di aplikasi FAQ."
        wa_link = f"https://wa.me/{wa_number}?text={wa_text.replace(' ', '%20')}"
        
        st.markdown(f'''
        <a href="{wa_link}" target="_blank" style="text-decoration: none;">
            <button style="
                background-color: #25D366; 
                color: white; 
                padding: 10px 20px; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer;
                font-weight: bold;
                font-size: 16px;
                display: flex;
                align_items: center;
                gap: 8px;">
                📱 Chat WhatsApp Support
            </button>
        </a>
        ''', unsafe_allow_html=True)
    else:
        st.info("👋 Selamat Datang. Database siap digunakan.")
else:
    st.markdown(f"**Menampilkan {start_idx+1}-{min(end_idx, total_docs)} dari {total_docs} data**")
    
    for item in page_data:
        # Badge Warna Modul
        tag = item.get('tag', 'Umum')
        badge_color = get_badge_color_name(tag)
        
        # Indikator Relevansi
        score_md = ""
        if item.get('score'):
            sc = item['score']
            
            if sc > HIGH_RELEVANCE_THRESHOLD:
                score_md = f":green[**({sc:.0f}% Relevansi) 🌟**]"
            elif sc > MEDIUM_RELEVANCE_THRESHOLD:
                score_md = f":green[({sc:.0f}% Relevansi)]"
            elif sc > RELEVANCE_THRESHOLD:
                score_md = f":orange[({sc:.0f}% Relevansi)]"
            else:
                score_md = f":red[({sc:.0f}% Relevansi)]"
        
        label = f":{badge_color}-background[{tag}] **{item.get('judul')}** {score_md}"
        
        with st.expander(label):
            render_mixed_content(item.get('jawaban_tampil', '-'), item.get('path_gambar'))
            
            src_raw = item.get('sumber_url')
            if src_raw and len(str(src_raw)) > 3:
                src = str(src_raw).strip()
                if "http" in src and " " not in src:
                    st.markdown(f"🔗 [Buka Sumber Referensi]({src})")
                else:
                    st.markdown(f"🔗 **Sumber:** {src}")

    # Pagination controls
    if total_pages > 1:
        st.markdown("---")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.session_state.page > 0:
                if st.button("⬅️ Sebelumnya"):
                    st.session_state.page -= 1
                    st.rerun()
        with c3:
            if st.session_state.page < total_pages - 1:
                if st.button("Berikutnya ➡️"):
                    st.session_state.page += 1
                    st.rerun()
