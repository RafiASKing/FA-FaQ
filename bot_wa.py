import os
import requests
import uvicorn
from fastapi import FastAPI, Request, BackgroundTasks
from dotenv import load_dotenv
from src import database, config

# Load Environment Variables
load_dotenv()

app = FastAPI()

# --- CONFIG ---
FONNTE_TOKEN = os.getenv("FONNTE_TOKEN")
# Ambil nomor bot sendiri dari config/env untuk logic group mention
# Jika tidak diset, default kosong (hati-hati logic group mungkin kurang akurat)
MY_BOT_NUMBER = os.getenv("BOT_NUMBER", "") 

if not FONNTE_TOKEN:
    print("⚠️ WARNING: FONNTE_TOKEN belum diisi di .env!")

def send_wa_reply(target, message):
    """Kirim pesan balasan via Fonnte API"""
    headers = {
        "Authorization": FONNTE_TOKEN,
    }
    # Fonnte support text markdown (Bold, Italic)
    data = {
        "target": target,
        "message": message,
    }

    try:
        url = "https://api.fonnte.com/send"
        resp = requests.post(url, headers=headers, data=data)
        print(f"✅ [Fonnte] Reply sent to {target} | Status: {resp.status_code}")
    except Exception as e:
        print(f"❌ [Fonnte] Error sending message: {e}")

def process_logic(sender, incoming_msg):
    """
    Otak Bot:
    1. Filter Group vs Private
    2. Search Database
    3. Generate Reply
    """
    
    # --- LOGIC GROUP HANDLING ---
    is_group = sender.endswith("@g.us")
    
    # Jika di Grup, bot HANYA menjawab jika di-mention
    # Asumsi user mengetik: "@628xxxx pertanyaan" atau tag bot
    if is_group:
        # Daftar panggilan biar bot nengok walau kontak disave aneh-aneh
            triggers = [
                "@bot", "@faq"           # Panggilan umum         # Panggilan ke admin
            ]
        
            # Tambahan: Nomor Asli (Jaga-jaga kalau user gak save kontak)
            if MY_BOT_NUMBER: triggers.append(f"@{MY_BOT_NUMBER}")
        
            # Cek apakah ada SALAH SATU kata di atas di pesan user
            is_mentioned = any(t in incoming_msg.lower() for t in triggers)

    # Bersihkan pesan (Hapus mention biar AI fokus ke pertanyaan)
    clean_msg = incoming_msg
    if is_group and MY_BOT_NUMBER:
        clean_msg = clean_msg.replace(f"@{MY_BOT_NUMBER}", "")
    
    clean_msg = clean_msg.replace("@bot", "").replace("@faq", "").strip()
    
    print(f"🧠 Processing: '{clean_msg}' from {sender}")

    # --- DATABASE SEARCH ---
    results = database.search_faq_for_bot(clean_msg, filter_tag="Semua Modul")
    
    reply_text = ""
    
    if not results or not results['ids'][0]:
        # Logic: Jika Private Chat, jawab sopan. Jika Group, diam (biar ga spam).
        if not is_group:
            reply_text = "🙏 Maaf, saya belum menemukan informasi terkait hal tersebut di SOP kami."
    else:
        # Ambil Top 1
        meta = results['metadatas'][0][0]
        dist = results['distances'][0][0]
        score = max(0, (1 - dist) * 100)
        
        # Cek Threshold Score
        if score >= config.BOT_MIN_SCORE:
            reply_text += f"🤖 *E-Assistant Response* (Akurasi: {score:.0f}%)\n\n"
            reply_text += f"📂 *Modul:* {meta['tag']}\n"
            reply_text += f"📌 *Topik:* {meta['judul']}\n\n"
            reply_text += f"{meta['jawaban_tampil']}\n"
            
            # Cek Gambar
            if meta.get('path_gambar') and str(meta.get('path_gambar')).lower() != 'none':
                reply_text += "\n🖼️ *[Gambar Terlampir]* Silakan cek Web App untuk visual."
                
            if meta.get('sumber_url'):
                reply_text += f"\n🔗 {meta.get('sumber_url')}"
        else:
            if not is_group:
                reply_text = "🤔 Pertanyaan kurang spesifik. Coba gunakan kata kunci lain."

    # --- SEND REPLY ---
    if reply_text:
        send_wa_reply(sender, reply_text)

@app.get("/")
def home():
    return {"status": "running", "service": "WhatsApp Bot Webhook"}

@app.post("/webhook")
async def fonnte_webhook(request: Request, background_tasks: BackgroundTasks):
    """Endpoint yang ditembak oleh Fonnte"""
    try:
        body = await request.json()
        
        sender = body.get("sender")
        message = body.get("message")
        
        # Validasi sederhana
        if sender and message and body.get("device_status") != "connect":
            # Jalankan di background agar response webhook cepat 200 OK
            background_tasks.add_task(process_logic, sender, message)
            
        return {"status": "ok"}
    except Exception as e:
        print(f"Error Webhook: {e}")
        return {"status": "error"}

if __name__ == "__main__":
    # Ini untuk run manual tanpa Docker
    uvicorn.run("bot_wa:app", host="0.0.0.0", port=8000, reload=True)