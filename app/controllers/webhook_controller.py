"""
Webhook Controller - Handler untuk WhatsApp webhook.
"""

import time
from fastapi import APIRouter, Request, BackgroundTasks, Header
from typing import Optional

from app.schemas import WebhookResponse
from app.services import WhatsAppService, SearchService
from app.services.agent_service import AgentService
from config.middleware import limiter
from core.content_parser import ContentParser
from core.logger import log, log_failed_search, log_search
from core.group_config import GroupConfig, is_group_message
from core.bot_config import BotConfig
from config.settings import settings
from config.constants import RELEVANCE_THRESHOLD, HIGH_RELEVANCE_THRESHOLD


router = APIRouter(prefix="/webhook", tags=["Webhook"])


class WebhookController:
    """Controller untuk WhatsApp webhook."""
    
    @staticmethod
    async def process_message(
        remote_jid: str,
        sender_name: str,
        message_body: str,
        is_group: bool,
        mentioned_list: list,
        group_name: str = "",
        has_image: bool = False,
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

        search_mode = BotConfig.get_search_mode()
        
        # === GROUP MODULE WHITELIST ===
        allowed_modules = None  # None = all modules (for DM)
        
        if is_group and is_group_message(remote_jid):
            # Get group display name (priority: payload > API > fallback)
            group_display_name = group_name
            
            if not group_display_name:
                # Try fetching from WPPConnect API
                try:
                    from config import container
                    messaging = container.get_messaging()
                    api_name = messaging.get_group_name(remote_jid)
                    if api_name:
                        group_display_name = api_name
                        log(f"📛 Got group name from API: {api_name}")
                except Exception as e:
                    log(f"⚠️ Failed to get group name from API: {e}")
            
            # Ultimate fallback
            if not group_display_name:
                group_display_name = f"Group {remote_jid[:20]}..."
            
            # Auto-register group on first mention
            GroupConfig.register_group(remote_jid, group_display_name)
            
            # Get allowed modules for this group
            allowed_modules = GroupConfig.get_allowed_modules(remote_jid)
            log(f"📋 Group modules: {allowed_modules}")
        
        # Bersihkan query dan cap length
        clean_query = WhatsAppService.clean_query(message_body)
        if clean_query:
            clean_query = clean_query[:1000]

        if has_image:
            if search_mode == "agent_pro":
                WhatsAppService.send_text(
                    remote_jid,
                    "📸 Agent Pro untuk analisis gambar sedang dalam pengembangan. Untuk sekarang, bot akan memproses caption/teks pertanyaan Anda dulu."
                )
            elif search_mode == "agent":
                WhatsAppService.send_text(
                    remote_jid,
                    "📸 Agent Flash saat ini belum mendukung analisis gambar. Bot akan memproses caption/teks pertanyaan Anda dulu."
                )
            else:
                WhatsAppService.send_text(
                    remote_jid,
                    "📸 Mode Immediate saat ini belum mendukung analisis gambar. Bot akan memproses caption/teks pertanyaan Anda dulu."
                )

        if not clean_query:
            if has_image or WhatsAppService.is_non_text_payload(message_body):
                WhatsAppService.send_text(
                    remote_jid,
                    f"Halo {sender_name}, gambar terdeteksi. Mohon sertakan caption/teks pertanyaan agar bisa diproses."
                )
            else:
                WhatsAppService.send_text(
                    remote_jid,
                    f"Halo {sender_name}, silakan ketik pertanyaan Anda."
                )
            return

        # Send acknowledgment for agent modes (immediate is fast enough, no need)
        if search_mode == "agent_pro":
            WhatsAppService.send_text(remote_jid, "Baik, mohon ditunggu...")
        elif search_mode == "agent":
            WhatsAppService.send_text(remote_jid, "Baik, mohon ditunggu")
        
        log(f"🔍 Mencari: '{clean_query}' (mode: {search_mode})")
        
        # Search with mode selection + timing
        t_start = time.time()
        try:
            if search_mode in ("agent", "agent_pro"):
                use_pro = search_mode == "agent_pro"
                result = AgentService.grade_search(clean_query, allowed_modules, use_pro=use_pro)
                results = [result] if result else []
            else:
                results = SearchService.search_for_bot(
                    clean_query,
                    allowed_modules=allowed_modules
                )
        except Exception as e:
            log(f"❌ Search error: {e}")
            WhatsAppService.send_text(remote_jid, "Maaf, terjadi gangguan saat mencari.")
            return
        response_ms = int((time.time() - t_start) * 1000)
        
        web_url = settings.web_v2_url
        
        if not results:
            # Get rejected top-1 for diagnostics (no threshold)
            rejected = SearchService.search(clean_query, n_results=1, min_score=0)
            if rejected:
                r = rejected[0]
                log_failed_search(
                    clean_query, reason="below_threshold", mode=search_mode,
                    top_score=r.score, top_faq_id=r.id, top_faq_title=r.judul,
                    response_ms=response_ms, source="whatsapp",
                    detail=f"Best candidate scored {r.score:.1f}%",
                )
            else:
                log_failed_search(
                    clean_query, reason="no_results", mode=search_mode,
                    response_ms=response_ms, source="whatsapp",
                )
            log_search(clean_query, score=0, mode=search_mode, response_ms=response_ms)

            fail_msg = f"Maaf, tidak ditemukan hasil yang relevan untuk: '{clean_query}'\n\n"
            fail_msg += f"Silakan cari manual di: {web_url}"
            WhatsAppService.send_text(remote_jid, fail_msg)
            return

        # Ambil hasil terbaik
        top_result = results[0]
        score = top_result.score

        # Threshold check ONLY for immediate mode
        if search_mode == "immediate" and score < RELEVANCE_THRESHOLD:
            log_failed_search(
                clean_query, reason="below_threshold", mode=search_mode,
                top_score=score, top_faq_id=top_result.id,
                top_faq_title=top_result.judul, response_ms=response_ms,
                source="whatsapp",
                detail=f"Score {score:.1f}% < threshold {RELEVANCE_THRESHOLD}%",
            )
            log_search(clean_query, score=score, faq_id=top_result.id,
                       faq_title=top_result.judul, mode=search_mode, response_ms=response_ms)
            
            msg = f"Maaf, belum ada data yang cocok.\n\n"
            msg += f"Coba tanya lebih spesifik atau cek FaQs lengkap di: {web_url}"
            WhatsAppService.send_text(remote_jid, msg)
            return
        
        # Log successful search
        log_search(clean_query, score=score, faq_id=top_result.id,
                   faq_title=top_result.judul, mode=search_mode, response_ms=response_ms)
        
        # Build response header
        if search_mode == "agent_pro":
            header = f"💎 Relevansi: {score:.0f}%\n"
        elif search_mode == "agent":
            header = f"Relevansi: {score:.0f}%\n"
        elif score >= HIGH_RELEVANCE_THRESHOLD:
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
    @limiter.limit("120/minute")
    async def whatsapp_webhook(
        request: Request,
        background_tasks: BackgroundTasks,
        x_webhook_secret: Optional[str] = Header(None),
    ):
        """
        Endpoint untuk menerima webhook dari WPPConnect.
        Protected by optional WEBHOOK_SECRET header validation.
        """
        # Validate webhook secret if configured
        if settings.webhook_secret:
            if x_webhook_secret != settings.webhook_secret:
                log("⚠️ Webhook rejected: invalid secret")
                return WebhookResponse(status="error", message="Invalid webhook secret")
        
        try:
            body = await request.json()

            # Metadata-only debug log (safe: no raw payload/base64 printed)
            if isinstance(body, dict):
                data = body.get("data") if isinstance(body.get("data"), dict) else {}

                body_text = data.get("body") or body.get("body") or ""
                caption_text = data.get("caption") or body.get("caption") or ""
                content_text = data.get("content") or body.get("content") or ""
                mentioned = data.get("mentionedJidList") or body.get("mentionedJidList") or []
                if not isinstance(mentioned, list):
                    mentioned = []

                raw_msg_id = data.get("id") or body.get("id") or ""
                msg_id = str(raw_msg_id)[:24] if raw_msg_id else "-"

                raw_remote = (
                    data.get("from")
                    or data.get("chatId")
                    or body.get("from")
                    or body.get("chatId")
                    or ""
                )
                remote = str(raw_remote)
                remote_masked = f"...{remote[-14:]}" if remote else "-"

                body_len = len(str(body_text)) if body_text else 0
                caption_len = len(str(caption_text)) if caption_text else 0
                content_len = len(str(content_text)) if content_text else 0

                body_str = str(body_text).strip() if body_text else ""
                is_base64_jpeg = body_str.startswith("/9j/") and body_len >= 120
                is_data_image = body_str.lower().startswith("data:image/")

                mime = data.get("mimetype") or data.get("mimeType") or body.get("mimetype") or ""
                msg_type = data.get("type") or body.get("type") or ""

                data_keys = sorted([k for k in data.keys() if isinstance(k, str)])[:12]
                client_ip = request.client.host if request.client else "-"

                log(
                    "🧾 WEBHOOK_DBG "
                    f"ip={client_ip} "
                    f"event={body.get('event', '-')} "
                    f"msg_id={msg_id} "
                    f"from={remote_masked} "
                    f"body_len={body_len} "
                    f"caption_len={caption_len} "
                    f"content_len={content_len} "
                    f"mentioned_count={len(mentioned)} "
                    f"base64_jpeg={is_base64_jpeg} "
                    f"data_image={is_data_image} "
                    f"mime={mime or '-'} "
                    f"type={msg_type or '-'} "
                    f"data_keys={data_keys}"
                )
            else:
                log(f"🧾 WEBHOOK_DBG payload_type={type(body).__name__}")
            
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
            group_name = payload.get_group_name()
            has_image = payload.has_image_payload()
            
            if not remote_jid:
                return WebhookResponse(status="ignored", message="No remote JID")
            
            # Process in background
            background_tasks.add_task(
                WebhookController.process_message,
                remote_jid,
                sender_name,
                message_body,
                is_group,
                mentioned_list,
                group_name,
                has_image
            )
            
            return WebhookResponse(status="success", message="Message queued")
            
        except Exception as e:
            log(f"❌ Webhook Error: {e}")
            return WebhookResponse(status="error", message=str(e))
