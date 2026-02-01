"""
Webhook Controller - Handler untuk WhatsApp webhook.
"""

import time
from fastapi import APIRouter, Request, BackgroundTasks

from app.schemas import WebhookResponse
from app.services import WhatsAppService, SearchService
from core.content_parser import ContentParser
from core.logger import log, log_failed_search
from config.settings import settings
from config.constants import RELEVANCE_THRESHOLD


router = APIRouter(prefix="/webhook", tags=["Webhook"])


class WebhookController:
    """Controller untuk WhatsApp webhook."""
    
    @staticmethod
    async def process_message(
        remote_jid: str,
        sender_name: str,
        message_body: str,
        is_group: bool,
        mentioned_list: list
    ):
        """
        Background task untuk memproses pesan masuk.
        """
        log(f"⚙️ Memproses Pesan: '{message_body}' dari {sender_name} (Group: {is_group})")
        
        # Check apakah harus reply
        should_reply = WhatsAppService.should_reply_to_message(
            is_group, message_body, mentioned_list
        )
        
        if not should_reply:
            return
        
        # Bersihkan query
        clean_query = WhatsAppService.clean_query(message_body)
        
        if not clean_query:
            WhatsAppService.send_text(
                remote_jid, 
                f"Halo {sender_name}, silakan ketik pertanyaan Anda."
            )
            return
        
        log(f"🔍 Mencari: '{clean_query}'")
        
        # Search
        try:
            results = SearchService.search_for_bot(clean_query)
        except Exception as e:
            log(f"❌ Database error: {e}")
            WhatsAppService.send_text(remote_jid, "Maaf, database sedang gangguan.")
            return
        
        web_url = settings.web_v2_url
        
        if not results:
            # Log failed search
            log_failed_search(clean_query)
            
            fail_msg = f"Maaf, tidak ditemukan hasil yang relevan untuk: '{clean_query}'\n\n"
            fail_msg += f"Silakan cari manual di: {web_url}"
            WhatsAppService.send_text(remote_jid, fail_msg)
            return
        
        # Ambil hasil terbaik
        top_result = results[0]
        score = top_result.score
        
        if score < RELEVANCE_THRESHOLD:
            log_failed_search(clean_query)
            
            msg = f"Maaf, belum ada data yang cocok.\n\n"
            msg += f"Coba tanya lebih spesifik atau cek FaQs lengkap di: {web_url}"
            WhatsAppService.send_text(remote_jid, msg)
            return
        
        # Build response
        if score >= 60:
            header = f"Relevansi: {score:.0f}%\n"
        else:
            header = f"[Relevansi Rendah: {score:.0f}%]\n"
        
        judul = top_result.judul
        jawaban_raw = top_result.jawaban_tampil
        
        # Parse gambar untuk WhatsApp
        processed_text, images_to_send = ContentParser.to_whatsapp(
            jawaban_raw, top_result.path_gambar
        )
        
        # Susun pesan
        final_text = f"{header}\n"
        final_text += f"*{judul}*\n\n"
        final_text += processed_text
        
        # Tambah sumber jika ada
        sumber = str(top_result.sumber_url).strip() if top_result.sumber_url else ""
        if len(sumber) > 3:
            if "http" in sumber.lower():
                final_text += f"\n\n\nSumber: {sumber}"
            else:
                final_text += f"\n\n\nNote: {sumber}"
        
        # Kirim jawaban teks
        WhatsAppService.send_text(remote_jid, final_text)
        
        # Kirim gambar
        if images_to_send:
            WhatsAppService.send_images(remote_jid, images_to_send)
        
        # Kirim footer
        time.sleep(0.5)
        footer_text = "------------------------------\n"
        footer_text += "Jika bukan ini jawaban yang dimaksud:\n\n"
        footer_text += f"1. Cek Library Lengkap: {web_url}\n"
        footer_text += "2. Atau gunakan *kalimat* spesifik beserta nama modul/topik (misal: IPD/ED/Jadwal).\n"
        footer_text += "Contoh: \n\"Gimana cara edit obat di EMR ED Pharmacy?\""
        
        WhatsAppService.send_text(remote_jid, footer_text)
    
    @staticmethod
    @router.post("/whatsapp", response_model=WebhookResponse)
    async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
        """
        Endpoint untuk menerima webhook dari WPPConnect.
        """
        try:
            body = await request.json()
            
            # Parse payload
            from app.schemas import WhatsAppWebhookPayload
            payload = WhatsAppWebhookPayload(**body)
            
            # Check apakah harus diproses
            if not payload.should_process():
                return WebhookResponse(status="ignored", message="Event ignored")
            
            # Extract data
            remote_jid = payload.get_remote_jid()
            message_body = payload.get_message_body()
            sender_name = payload.get_sender_name()
            is_group = payload.is_group_message()
            mentioned_list = payload.get_mentioned_list()
            
            if not remote_jid:
                return WebhookResponse(status="ignored", message="No remote JID")
            
            # Process in background
            background_tasks.add_task(
                WebhookController.process_message,
                remote_jid,
                sender_name,
                message_body,
                is_group,
                mentioned_list
            )
            
            return WebhookResponse(status="success", message="Message queued")
            
        except Exception as e:
            log(f"❌ Webhook Error: {e}")
            return WebhookResponse(status="error", message=str(e))
