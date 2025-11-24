import os
import sys

# Setup path agar bisa import dari folder src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src import database
# IMPORT CONFIG DARI SINI
from src.config import BOT_MIN_SCORE, BOT_MIN_GAP

def simulasi_otak_bot(raw_text, filter_tag="Semua Modul"):
    # 1. BERSIHKAN INPUT
    clean_query = raw_text.replace("@botFaQ", "").replace("@botfaq", "").strip()
    
    if not clean_query:
        return "⚠️ Masukkan pertanyaan setelah @botFaQ."

    print(f"\n🧠 Sedang memproses: '{clean_query}' [Tag: {filter_tag}]...")

    # 2. PANGGIL DATABASE
    results = database.search_faq_for_bot(clean_query, filter_tag)

    if not results or not results['ids'][0]:
        return "❌ Maaf, tidak ditemukan data yang relevan di database."

    # 3. EXTRACTION & SCORING
    candidates = []
    for i in range(len(results['ids'][0])):
        meta = results['metadatas'][0][i]
        dist = results['distances'][0][i]
        score = max(0, (1 - dist) * 100)
        
        # Cek apakah ada gambar
        has_image = False
        img_path = meta.get('path_gambar', 'none')
        if img_path and str(img_path).lower() != 'none':
            has_image = True

        candidates.append({
            "score": score,
            "judul": meta.get('judul'),
            "tag": meta.get('tag'),
            "jawaban": meta.get('jawaban_tampil'),
            "url": meta.get('sumber_url', '-'),
            "has_image": has_image
        })

    top1 = candidates[0]
    top2 = candidates[1] if len(candidates) > 1 else None

    # ==========================================
    # 🚀 LOGIKA CERDAS (PAKE CONFIG ENV)
    # ==========================================
    
    is_winner_absolute = False
    
    # Gunakan Variabel dari Config
    if top1['score'] >= BOT_MIN_SCORE:
        if top2:
            gap = top1['score'] - top2['score']
            if gap >= BOT_MIN_GAP: # Cek Gap dari Config
                is_winner_absolute = True
                print(f"DEBUG: Winner Mutlak! Score: {top1['score']:.1f}, Gap: {gap:.1f}")
            else:
                print(f"DEBUG: Score tinggi tapi saingan ketat. Gap cuma {gap:.1f}")
        else:
            is_winner_absolute = True

    # ==========================================
    # 📤 OUTPUT GENERATION
    # ==========================================

    response_text = ""

    if is_winner_absolute:
        response_text += f"🎯 *SOLUSI DITEMUKAN* (Akurasi: {top1['score']:.0f}%)\n"
        response_text += f"📂 Modul: {top1['tag']}\n\n"
        response_text += f"*{top1['judul']}*\n"
        response_text += f"{top1['jawaban']}\n\n"
        
        # Tambahan Indikator Gambar
        if top1['has_image']:
            response_text += "🖼️ *[Gambar Terlampir]*\n\n"
            
        if top1['url'] and len(top1['url']) > 3:
             response_text += f"🔗 Sumber: {top1['url']}"

    else:
        response_text += "🔍 *MUNGKIN INI YANG KAMU CARI:*\n"
        if top1['score'] < 25:
             response_text += "(Relevansi rendah, coba kata kunci lain)\n"
        
        limit = min(3, len(candidates))
        for i in range(limit):
            c = candidates[i]
            icon = "1️⃣" if i == 0 else ("2️⃣" if i == 1 else "3️⃣")
            link_txt = f" (🔗 {c['url']})" if (c['url'] and len(c['url'])>3) else ""
            img_icon = " 🖼️" if c['has_image'] else ""
            
            response_text += f"\n{icon} *[{c['tag']}] {c['judul']}*{img_icon} {link_txt}"
            response_text += f"\n   └─ Relevansi: {c['score']:.1f}%"
    
    return response_text

if __name__ == "__main__":
    print("="*50)
    print("🤖 TEST BOT SIMULATOR (LOCAL)")
    print(f"⚙️ Config Loaded: Min Score={BOT_MIN_SCORE}, Min Gap={BOT_MIN_GAP}")
    print("="*50)
    
    CURRENT_TAG_CONTEXT = "Semua Modul" 

    while True:
        try:
            user_input = input("\n💬 User: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            balasan = simulasi_otak_bot(user_input, filter_tag=CURRENT_TAG_CONTEXT)
            print("-" * 20)
            print("🤖 Bot:\n" + balasan)
            print("-" * 20) 
        except KeyboardInterrupt:
            break