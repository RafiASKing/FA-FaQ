import os
import requests
import uvicorn
import re
import base64
import mimetypes
from fastapi import FastAPI, Request, BackgroundTasks
from dotenv import load_dotenv
from src import database

# Load Environment Variables
load_dotenv()

app = FastAPI()

# --- KONFIGURASI WPPCONNECT ---
# Sesuai dengan docker-compose yang baru
WA_BASE_URL = os.getenv("WA_BASE_URL", "http://wppconnect:21465")
WA_SESSION_KEY = os.getenv("WA_SESSION_KEY", "admin123") # Secret Key
WA_SESSION_NAME = "mysession" # Nama sesi default

# Headers untuk Auth WPPConnect
HEADERS = {
    "Authorization": f"Bearer {WA_SESSION_KEY}",
    "Content-Type": "application/json"
}

def get_base64_image(file_path):
    """
    Encode gambar lokal ke Base64 dengan Data URI Scheme.
    WPPConnect WAJIB pakai format: 'data:image/jpeg;base64,.....'
    """
    try:
        clean_path = file_path.replace("\\", "/")
        if not os.path.exists(clean_path): 
            print(f"❌ Gambar tidak ditemukan: {clean_path}")
            return None, None
        
        # Deteksi Mime Type (jpg/png/dll)
        mime_type, _ = mimetypes.guess_type(clean_path)
        if not mime_type: mime_type = "image/jpeg"

        with open(clean_path, "rb") as image_file:
            raw_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            
        # Format lengkap untuk WPPConnect
        full_data_uri = f"data:{mime_type};base64,{raw_base64}"
        filename = os.path.basename(clean_path)
        
        return full_data_uri, filename
    except Exception as e:
        print(f"❌ Gagal encode gambar: {e}")
        return None, None

def send_wpp_text(phone, message):
    """Kirim Teks via WPPConnect"""
    url = f"{WA_BASE_URL}/api/{WA_SESSION_NAME}/send-message"
    
    payload = {
        "phone": phone,
        "message": message,
        "isGroup": False # Default false, WPPConnect otomatis deteksi dari nomor @g.us
    }
    
    try:
        r = requests.post(url, json=payload, headers=HEADERS)
        if r.status_code == 201 or r.status_code == 200:
            # print(f"📤 Sent Text ke {phone}")
            pass
        else:
            print(f"❌ Gagal Kirim Teks: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Error Connection Text: {e}")

def send_wpp_image(phone, file_path, caption=""):
    """Kirim Gambar via WPPConnect"""
    url = f"{WA_BASE_URL}/api/{WA_SESSION_NAME}/send-image"
    
    base64_str, filename = get_base64_image(file_path)
    if not base64_str: return

    payload = {
        "phone": phone,
        "base64": base64_str,
        "caption": caption,
        "isGroup": False
    }
    
    try:
        r = requests.post(url, json=payload, headers=HEADERS)
        if r.status_code == 201 or r.status_code == 200:
            print(f"🖼️ Sent Image ke {phone}")
        else:
            print(f"❌ Gagal Kirim Gambar: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Error Connection Image: {e}")

def process_logic(remote_jid, sender_name, message_body, is_group, has_mention):
    """
    LOGIKA BOT (Sama seperti sebelumnya, tapi panggil fungsi WPP)
    """
    
    # 1. LOGIKA TRIGGER
    should_reply = False
    
    if not is_group:
        should_reply = True # PC Selalu balas
    else:
        # Group logic
        if has_mention:
            should_reply = True
        elif "@faq" in message_body.lower():
            should_reply = True
            
    if not should_reply: return

    # 2. CLEANING QUERY
    clean_query = message_body.replace("@faq", "").strip()
    clean_query = re.sub(r'@\d+', '', clean_query).strip()

    if not clean_query:
        send_wpp_text(remote_jid, f"Halo {sender_name}, silakan ketik pertanyaanmu.")
        return

    print(f"🔍 Searching: '{clean_query}' (From: {sender_name})")

    # 3. SEARCH DATABASE
    try:
        results = database.search_faq_for_bot(clean_query, filter_tag="Semua Modul")
    except Exception as e:
        print(f"Database Error: {e}")
        send_wpp_text(remote_jid, "Maaf, sedang ada gangguan pada database.")
        return
    
    reply_text = ""
    list_gambar_to_send = []

    if not results or not results['ids'][0]:
        reply_text = f"🙏 Maaf {sender_name}, tidak ditemukan jawaban untuk: *'{clean_query}'*."
        send_wpp_text(remote_jid, reply_text)
        return
    else:
        # Ambil Top 1
        meta = results['metadatas'][0][0]
        dist = results['distances'][0][0]
        score = max(0, (1 - dist) * 100)

        if score < 60:
             reply_text = f"🤔 Kurang yakin ({score:.0f}%):\n\n"
        else:
             reply_text = f"🤖 *FAQ Assistant* ({score:.0f}%)\n\n"

        judul = meta['judul']
        jawaban_raw = meta['jawaban_tampil']
        
        # 4. PARSING GAMBAR
        raw_paths = meta.get('path_gambar', 'none')
        img_db_list = []
        if raw_paths and str(raw_paths).lower() != 'none':
             paths = raw_paths.split(';')
             for p in paths:
                 img_db_list.append(p.strip().replace("\\", "/"))

        # Fungsi ganti tag [GAMBAR X]
        def replace_tag(match):
            try:
                idx = int(match.group(1)) - 1
                if 0 <= idx < len(img_db_list):
                    list_gambar_to_send.append(img_db_list[idx])
                    return f"*( 👇 Lihat Gambar {idx+1} )*"
                return ""
            except: return ""

        jawaban_processed = re.sub(r'\[GAMBAR\s*(\d+)\]', replace_tag, jawaban_raw, flags=re.IGNORECASE)
        
        # Fallback gambar
        if not list_gambar_to_send and img_db_list:
            list_gambar_to_send = img_db_list

        # Susun Pesan
        reply_text += f"❓ *{judul}*\n✅ {jawaban_processed}\n"
        if meta.get('sumber_url'): reply_text += f"\n🔗 {meta.get('sumber_url')}"

        # 5. KIRIM HASIL KE WPPCONNECT
        send_wpp_text(remote_jid, reply_text)
        
        # Kirim Gambar
        for i, img_path in enumerate(list_gambar_to_send):
            send_wpp_image(remote_jid, img_path, caption=f"Gambar #{i+1}")

@app.post("/webhook")
async def wpp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook Handler KHUSUS WPPConnect
    Struktur JSON WPPConnect berbeda dengan Evolution
    """
    try:
        body = await request.json()
        
        # WPPConnect biasanya mengirim event 'onMessage'
        # Struktur umum: { "event": "onMessage", "session": "...", "data": { ... } }
        
        event = body.get("event")
        data = body.get("data", {}) # Isi pesan ada di sini
        
        # Hanya proses pesan masuk
        if event != "onMessage":
            return {"status": "ignored_event"}
            
        # 1. Cek Pesan Diri Sendiri
        if data.get("fromMe", False) is True:
            return {"status": "ignored_self"}

        # 2. Ambil Data Penting
        # 'from' di WPPConnect adalah nomor pengirim (misal 628123...@c.us)
        remote_jid = data.get("from")
        
        # Abaikan status broadcast
        if "status@broadcast" in remote_jid: return {"status": "ignored_status"}

        # 3. Ambil Isi Pesan (Body)
        message_body = data.get("body", "") or data.get("content", "")
        # Jika gambar dengan caption
        if data.get("type") == "image":
            message_body = data.get("caption", "")

        # 4. Ambil Nama Pengirim
        sender_obj = data.get("sender", {})
        sender_name = sender_obj.get("pushname") or sender_obj.get("name") or "User"

        # 5. Cek Group
        is_group = data.get("isGroupMsg", False)

        # 6. Cek Mention (Khusus WPPConnect)
        has_mention = False
        mentioned_list = data.get("mentionedJidList", [])
        
        # Logika sederhana: Jika bot ada di grup, dan ada mention, anggap user manggil bot
        # (Karena kita belum simpan nomor bot sendiri di variabel)
        if mentioned_list:
            has_mention = True

        # Jalankan Logika di Background
        background_tasks.add_task(
            process_logic, 
            remote_jid, 
            sender_name, 
            message_body, 
            is_group, 
            has_mention
        )
            
        return {"status": "success"}

    except Exception as e:
        print(f"Webhook Error: {e}")
        return {"status": "error"}

@app.on_event("startup")
async def startup_event():
    """
    Saat bot nyala, coba start session WPPConnect otomatis
    """
    print("🚀 Memulai Bot & Mencoba Start Session WPPConnect...")
    try:
        url = f"{WA_BASE_URL}/api/{WA_SESSION_NAME}/start-session"
        # Gunakan token session key jika diperlukan config webhook
        payload = {
            "webhook": "http://faq-bot:8000/webhook" # Register webhook otomatis
        }
        requests.post(url, json=payload, headers=HEADERS)
        print(f"✅ Sesi '{WA_SESSION_NAME}' diinisialisasi.")
    except:
        print("⚠️ Gagal auto-start session (Mungkin server WPP belum siap).")

@app.get("/")
def home():
    return {"status": "WPPConnect Bot Running", "engine": "WPPConnect"}

if __name__ == "__main__":
    uvicorn.run("bot_wa:app", host="0.0.0.0", port=8000)