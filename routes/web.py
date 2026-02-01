"""
Web Routes - HTML template routes untuk Web V2.
"""

import math
import re
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config.settings import paths
from config.constants import ITEMS_PER_PAGE, WEB_TOP_RESULTS
from app.services import SearchService
from core.content_parser import ContentParser
from core.tag_manager import TagManager


router = APIRouter(tags=["Web"])

# Setup templates
templates = Jinja2Templates(directory=str(paths.TEMPLATES_DIR))


def process_content_to_html(text_markdown: str, img_path_str: str) -> str:
    """
    Convert konten FAQ ke HTML untuk rendering di template.
    """
    return ContentParser.to_html(text_markdown, img_path_str)


def process_source_html(sumber_url: str) -> str:
    """
    Generate HTML untuk sumber/referensi.
    """
    src = str(sumber_url).strip() if sumber_url else ""
    
    if len(src) <= 3:
        return ""
    
    if "http" in src and " " not in src:
        return (
            f'<div class="source-box"><a href="{src}" target="_blank">'
            "🔗 Buka Sumber Referensi</a></div>"
        )
    else:
        # Handle URL dalam teks
        linked_src = re.sub(
            r'(https?://\S+)', 
            r'<a href="\1" target="_blank">\1</a>', 
            src
        )
        return f'<div class="source-box">🔗 {linked_src}</div>'


@router.get("/", response_class=HTMLResponse)
async def read_root(
    request: Request, 
    q: str = "", 
    tag: str = "Semua Modul", 
    page: int = 0
):
    """
    Main page - Search dan Browse FAQ.
    """
    results = []
    total_pages = 1
    is_search_mode = False
    
    # Ambil list tag untuk dropdown
    try:
        db_tags = SearchService.get_unique_tags()
    except:
        db_tags = []
    all_tags = ["Semua Modul"] + (db_tags if db_tags else [])
    
    # === SEARCH MODE ===
    if q.strip():
        is_search_mode = True
        
        search_results = SearchService.search_for_web(q, tag if tag != "Semua Modul" else None, WEB_TOP_RESULTS)
        
        for r in search_results:
            results.append({
                'id': r.id,
                'tag': r.tag,
                'judul': r.judul,
                'jawaban_tampil': r.jawaban_tampil,
                'path_gambar': r.path_gambar,
                'sumber_url': r.sumber_url,
                'score': int(r.score),
                'score_class': r.score_class,
                'badge_color': r.badge_color
            })
    
    # === BROWSE MODE ===
    else:
        raw_all = SearchService.get_all_faqs(tag if tag != "Semua Modul" else None)
        
        # Hitung paginasi
        total_docs = len(raw_all)
        total_pages = math.ceil(total_docs / ITEMS_PER_PAGE) if total_docs > 0 else 1
        
        # Guard halaman
        if page >= total_pages:
            page = 0
        if page < 0:
            page = 0
        
        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        sliced_data = raw_all[start:end]
        
        for meta in sliced_data:
            tag_name = meta.get('tag', 'Umum')
            results.append({
                'id': meta.get('id', ''),
                'tag': tag_name,
                'judul': meta.get('judul', ''),
                'jawaban_tampil': meta.get('jawaban_tampil', ''),
                'path_gambar': meta.get('path_gambar', 'none'),
                'sumber_url': meta.get('sumber_url', ''),
                'score': None,  # Tidak ada score di browse mode
                'badge_color': TagManager.get_tag_color(tag_name)
            })
    
    # === PROCESS CONTENT ===
    for item in results:
        item['html_content'] = process_content_to_html(
            item.get('jawaban_tampil', ''),
            item.get('path_gambar', '')
        )
        item['source_html'] = process_source_html(item.get('sumber_url', ''))
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "results": results,
        "query": q,
        "current_tag": tag,
        "all_tags": all_tags,
        "page": page,
        "total_pages": total_pages,
        "is_search_mode": is_search_mode,
        "total_items": len(results)
    })
