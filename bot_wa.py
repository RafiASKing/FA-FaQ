import os
import requests
import uvicorn
from fastapi import FastAPI, Request, BackgroundTasks
from dotenv import load_dotenv
from src import database

# Load Environment Variables
load_dotenv()

app = FastAPI()

# --- CONFIG ---
FONNTE_TOKEN = os.getenv("FONNTE_TOKEN")

if not FONNTE_TOKEN:
    print("⚠️ WARNING: FONNTE_TOKEN belum diisi di .env!")

def send_wa_reply(target, message):
    """Kirim pesan balasan via Fonnte API"""
    headers = {
        "Authorization": FONNTE_TOKEN,
    }
    data = {
        "target": target,
        "message": message,
    }

    try:
        # Fonnte API Endpoint
        url = "https://api.fonnte.com/send"
        resp = requests.post(url, headers=headers, data=data)
        print(f"✅ [Fonnte] Sent to {target} | Status: {resp.status_code}")
    except Exception as e:
        print(f"❌ [Fonnte] Error: {e}")

def process_logic(sender, incoming_msg):
    """
    Logic Sederhana & Cepat:
    1. Cek ada '@faq' gak? Kalau gak ada, ABORKAN.
    2. Ambil teks sisanya sebagai query.
    3. Cari Top 1 di Database.
    4. Kirim Jawaban.
    """
    
    # 1. VALIDASI TRIGGER
    # Pakai lower() biar @FAQ atau @faq tetap masuk
    if "@faq" not in incoming_msg.lower():
        return # Skip, jangan diproses

    # 2. BERSIHKAN QUERY
    # Hapus @faq, sisa teksnya adalah query pencarian
    query = incoming_msg.lower().replace("@faq", "").strip()
    
    if not query:
        send_wa_reply(sender, "⚠️ Silakan ketik pertanyaan setelah @faq.\nContoh: *@faq cara login nurse*")
        return

    print(f"🔍 Searching: '{query}' from {sender}")

    # 3. CARI DI DATABASE (Rank 1 Only)
    # Filter selalu "Semua Modul" sesuai request
    results = database.search_faq_for_bot(query, filter_tag="Semua Modul")
    
    reply_text = ""
    
    # Cek apakah ada hasil
    if not results or not results['ids'][0]:
        reply_text = f"❌ Maaf, tidak ditemukan jawaban untuk: *'{query}'*\nCoba gunakan kata kunci lain."
    else:
        # AMBIL RANK 1 (Paling Relevan)
        meta = results['metadatas'][0][0]
        dist = results['distances'][0][0]
        score = max(0, (1 - dist) * 100) # Hitung skor persen
        
        # Format Jawaban: Judul & Isi
        reply_text += f"🤖 *FAQ Assistant* (Akurasi: {score:.0f}%)\n\n"
        reply_text += f"📂 Modul: *{meta['tag']}*\n"
        reply_text += f"❓ Tanya: *{meta['judul']}*\n"
        reply_text += f"✅ Jawab: \n{meta['jawaban_tampil']}\n"
        
        # Cek Gambar
        if meta.get('path_gambar') and str(meta.get('path_gambar')).lower() != 'none':
            reply_text += "\n🖼️ *[Ada Gambar]* Cek aplikasi Web untuk visual detail."
            
        # Cek Sumber URL
        if meta.get('sumber_url'):
            reply_text += f"\n🔗 Sumber: {meta.get('sumber_url')}"

    # 4. KIRIM BALASAN
    send_wa_reply(sender, reply_text)

@app.get("/")
def home():
    return {"status": "running", "mode": "Simple Bot @faq"}

@app.post("/webhook")
async def fonnte_webhook(request: Request, background_tasks: BackgroundTasks):
    """Jalur masuk pesan dari Fonnte"""
    try:
        body = await request.json()
        
        sender = body.get("sender")
        message = body.get("message")
        
        # Pastikan pesan valid & bukan status update dari device sendiri
        if sender and message and body.get("device_status") != "connect":
            # Jalankan di background biar Fonnte ga nunggu loading
            background_tasks.add_task(process_logic, sender, message)
            
        return {"status": "ok"}
    except Exception as e:
        print(f"Error Webhook: {e}")
        return {"status": "error"}

if __name__ == "__main__":
    # Port 8000 (Internal Container)
    uvicorn.run("bot_wa:app", host="0.0.0.0", port=8000)