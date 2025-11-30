import os
import requests
import uvicorn
import re
import base64
from fastapi import FastAPI, Request, BackgroundTasks
from dotenv import load_dotenv
from src import database, utils

# Load Environment Variables
load_dotenv()

app = FastAPI()

# Konfigurasi WAHA (Diambil dari docker-compose)
WAHA_BASE_URL = os.getenv("WAHA_BASE_URL", "http://waha:3000")

def get_base64_image(file_path):
    """
    Mengubah file gambar lokal menjadi Base64 string
    agar bisa dikirim lewat JSON ke WAHA (antar container).
    """
    try:
        # Bersihkan path (kadang ada ./images/...)
        clean_path = file_path.replace("\\", "/")
        if not os.path.exists(clean_path):
            print(f"❌ Gambar tidak ditemukan: {clean_path}")
            return None, None
            
        with open(clean_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        # Tentukan mime type sederhana
        mime_type = "image/jpeg"
        if clean_path.lower().endswith(".png"):
            mime_type = "image/png"
            
        # Format Data URI: "data:image/png;base64,....."
        return f"data:{mime_type};base64,{encoded_string}", os.path.basename(clean_path)
    except Exception as e:
        print(f"❌ Gagal encode gambar: {e}")
        return None, None

def send_waha_text(chat_id, text):
    """Kirim Pesan Teks via WAHA"""
    url = f"{WAHA_BASE_URL}/api/sendText"
    payload = {
        "chatId": chat_id,
        "text": text,
        "session": "default"
    }
    try:
        r = requests.post(url, json=payload)
        # print(f"📤 Sent Text to {chat_id}: {r.status_code}")
    except Exception as e:
        print(f"❌ Error Send Text: {e}")

def send_waha_image(chat_id, file_path, caption=""):
    """Kirim Gambar via WAHA (Base64 Mode)"""
    url = f"{WAHA_BASE_URL}/api/sendImage"
    
    # Encode gambar dulu
    data_uri, filename = get_base64_image(file_path)
    
    if not data_uri:
        return # Skip jika gambar rusak/hilang

    payload = {
        "chatId": chat_id,
        "file": {
            "mimetype": data_uri.split(";")[0].split(":")[1],
            "filename": filename,
            "data": data_uri.split(",")[1] # Ambil base64-nya saja
        },
        "caption": caption,
        "session": "default"
    }
    try:
        r = requests.post(url, json=payload)
        print(f"🖼️ Sent Image to {chat_id}: {r.status_code}")
    except Exception as e:
        print(f"❌ Error Send Image: {e}")

def process_logic(chat_id, sender_name, message_body, is_group, has_mention):
    """
    Otak Bot:
    1. Cek apakah perlu merespon (DM / Mention).
    2. Cari di Database.
    3. Format Text & Gambar.
    4. Kirim.
    """
    
    # === 1. LOGIKA TRIGGER (PENTING!) ===
    should_reply = False
    
    if not is_group:
        # Kalau Private Chat (PC), SELALU balas
        should_reply = True
    else:
        # Kalau Group, HANYA balas jika di-mention ATAU ada keyword trigger
        if has_mention:
            should_reply = True
        elif "@faq" in message_body.lower():
            should_reply = True
            
    if not should_reply:
        return # Abaikan chat ini

    # Bersihkan pesan dari @mention atau @faq
    # Biar query ke DB bersih
    clean_query = message_body.replace("@faq", "").strip()
    # (Opsional) Hapus mention tag WA style @628xxx
    clean_query = re.sub(r'@\d+', '', clean_query).strip()

    if not clean_query:
        send_waha_text(chat_id, f"Halo kak {sender_name}, ada yang bisa dibantu? Ketik masalahnya ya.")
        return

    print(f"🔍 Searching: '{clean_query}' for {chat_id}")

    # === 2. CARI DI DATABASE ===
    # Kita cari Top 1 saja biar bot fokus
    results = database.search_faq_for_bot(clean_query, filter_tag="Semua Modul")
    
    reply_text = ""
    list_gambar_to_send = []

    if not results or not results['ids'][0]:
        # Tidak ketemu
        reply_text = f"🙏 Maaf kak, saya belum punya jawaban untuk: *'{clean_query}'*.\nCoba kata kunci lain atau hubungi Admin."
        send_waha_text(chat_id, reply_text)
        return
    else:
        # KETEMU!
        meta = results['metadatas'][0][0]
        dist = results['distances'][0][0]
        score = max(0, (1 - dist) * 100)

        # Cek Score Kelayakan
        if score < 60: # Kalau relevansi rendah (bisa diatur)
             reply_text = f"🤔 Kurang yakin, tapi mungkin ini maksudnya (Relevansi {score:.0f}%):\n\n"
        else:
             reply_text = f"🤖 *FAQ Assistant* (Akurasi: {score:.0f}%)\n\n"

        judul = meta['judul']
        jawaban_raw = meta['jawaban_tampil']
        
        # === 3. PROCESSING GAMBAR (REQUEST KAMU) ===
        # Kita scan dulu apakah ada [GAMBAR X]
        
        # A. Ambil path gambar asli dari DB
        raw_paths = meta.get('path_gambar', 'none')
        img_db_list = []
        if raw_paths and str(raw_paths).lower() != 'none':
             # Split path (./images/ED/bla.png)
             paths = raw_paths.split(';')
             for p in paths:
                 clean_p = p.strip().replace("\\", "/")
                 img_db_list.append(clean_p)

        # B. Ganti Teks [GAMBAR X] -> (Lihat Gambar X)
        # Fungsi regex replacer
        def replace_tag(match):
            try:
                # match.group(1) adalah angkanya (misal "1")
                idx = int(match.group(1)) - 1
                if 0 <= idx < len(img_db_list):
                    # Masukkan ke antrian kirim
                    list_gambar_to_send.append(img_db_list[idx])
                    return f"*( 👇 Lihat Gambar {idx+1} di bawah )*"
                else:
                    return ""
            except: return ""

        # Lakukan replacement di teks jawaban
        jawaban_processed = re.sub(r'\[GAMBAR\s*(\d+)\]', replace_tag, jawaban_raw, flags=re.IGNORECASE)
        
        # C. Jika ada gambar tapi tidak ada tag di teks, kirim semua sebagai lampiran
        if not list_gambar_to_send and img_db_list:
            list_gambar_to_send = img_db_list

        # Susun Pesan Akhir
        reply_text += f"❓ *{judul}*\n"
        reply_text += f"✅ {jawaban_processed}\n"
        
        if meta.get('sumber_url') and len(meta.get('sumber_url')) > 3:
            reply_text += f"\n🔗 {meta.get('sumber_url')}"

        # === 4. KIRIM (TEKS DULU, BARU GAMBAR) ===
        send_waha_text(chat_id, reply_text)
        
        # Kirim Gambar (Looping)
        for i, img_path in enumerate(list_gambar_to_send):
            # Cek path lokal container
            # (Pastikan di docker-compose folder ./images sudah dimount ke /app/images)
            send_waha_image(chat_id, img_path, caption=f"Gambar Pendukung #{i+1}")


@app.post("/webhook")
async def waha_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook handler untuk WAHA.
    Menerima event 'message' dari WAHA.
    """
    try:
        body = await request.json()
        
        # Struktur WAHA biasanya: { "event": "message", "payload": { ... } }
        event_type = body.get("event")
        payload = body.get("payload", {})

        # Pastikan ini event pesan baru (bukan status update/ack)
        # 'message' atau 'message.upsert' tergantung versi WAHA, kita handle umum
        if event_type == "message":
            
            # Abaikan pesan dari status broadcast
            if payload.get("from") == "status@broadcast":
                return {"status": "ignored_status"}
            
            # Abaikan pesan dari diri sendiri (Bot)
            if payload.get("fromMe"):
                return {"status": "ignored_self"}

            # Ekstrak Data Penting
            chat_id = payload.get("from") # ID Pengirim (bisa group id atau user id)
            sender_name = payload.get("_data", {}).get("notifyName", "User")
            message_body = payload.get("body", "")
            
            # Cek Grup / Mention
            # isGroup bisa boolean true/false atau undefined
            is_group = "@g.us" in chat_id 
            
            # Cek Mention (WAHA kasih list mentionedIds)
            mentioned_ids = payload.get("mentionedIds", [])
            # Cek apakah bot saya (nomor WA yang dipasang) ada di list mention?
            # Cara gampang: kalau list mention gak kosong, anggap aja dimention (simplifikasi)
            # Atau cek logic WAHA 'hasMention' kalau ada (tergantung versi)
            has_mention = len(mentioned_ids) > 0 

            # Jalankan logic di background biar webhook fast response
            background_tasks.add_task(
                process_logic, 
                chat_id, 
                sender_name, 
                message_body, 
                is_group, 
                has_mention
            )
            
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Webhook Error: {e}")
        return {"status": "error"}

@app.get("/")
def home():
    return {"status": "WAHA Bot Running", "mode": "Direct Connection"}

if __name__ == "__main__":
    uvicorn.run("bot_wa:app", host="0.0.0.0", port=8000)