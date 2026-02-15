"""
Bot Tester - Streamlit app untuk simulasi WhatsApp Bot.

Simulasi bot logic tanpa perlu WPPConnect:
- Test private message vs group mode
- Test immediate vs agent mode
- Preview response yang akan dikirim bot
- Preview gambar yang akan di-attach
"""

import streamlit as st
import os
import time

# Import services directly (bypass webhook + WPPConnect)
from app.services.whatsapp_service import BotLogicService
from app.services.search_service import SearchService
from app.services.agent_service import AgentService
from core.content_parser import ContentParser
from core.tag_manager import TagManager
from config.constants import HIGH_RELEVANCE_THRESHOLD, MEDIUM_RELEVANCE_THRESHOLD
from core.image_handler import ImageHandler
from core.bot_config import BotConfig
from config.constants import BOT_TOP_RESULTS


st.set_page_config(
    page_title="🤖 Bot Tester",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 WhatsApp Bot Tester")
st.caption("Simulasi bot tanpa WPPConnect — supports Immediate & Agent mode!")

st.markdown("---")

# === INPUT SECTION ===
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    message = st.text_input(
        "💬 Pesan Masuk:",
        placeholder="Contoh: @faq cara daftar rawat jalan",
        help="Ketik pesan seperti yang dikirim user di WhatsApp"
    )

with col2:
    chat_mode = st.radio(
        "Chat Mode:",
        ["Private", "Group"],
        horizontal=True
    )

with col3:
    # Get current global mode
    global_mode = BotConfig.get_search_mode()
    mode_labels = ["⚡ Immediate", "🧠 Agent", "🧠💎 Pro"]
    mode_map = {"⚡ Immediate": "immediate", "🧠 Agent": "agent", "🧠💎 Pro": "agent_pro"}
    default_idx = 0 if global_mode == "immediate" else (2 if global_mode == "agent_pro" else 1)
    search_mode_label = st.radio(
        "Search Mode:",
        mode_labels,
        index=default_idx,
        horizontal=True
    )
    local_search_mode = mode_map[search_mode_label]

# Additional options for group mode
if chat_mode == "Group":
    st.info("💡 Di grup, bot hanya reply jika ada `@faq` di pesan atau di-mention langsung")

# === PROCESS BUTTON ===
if st.button("🔍 Test Bot Response", type="primary", use_container_width=True):
    if not message.strip():
        st.warning("⚠️ Ketik pesan dulu!")
    else:
        is_group = (chat_mode == "Group")
        
        # Step 1: Check if bot should reply
        should_reply = BotLogicService.should_reply_to_message(
            is_group=is_group,
            message_body=message,
            mentioned_list=[]  # Simulate no direct mention
        )
        
        st.markdown("---")
        st.subheader("📊 Bot Analysis")
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Chat Mode", "🏠 Private" if not is_group else "👥 Group")
        with col_b:
            mode_display = {"immediate": "⚡ Immediate", "agent": "🧠 Agent", "agent_pro": "🧠💎 Pro"}
            st.metric("Search Mode", mode_display.get(local_search_mode, local_search_mode))
        with col_c:
            if should_reply:
                st.metric("Decision", "✅ Will Reply")
            else:
                st.metric("Decision", "🔇 Will Ignore")
        
        if not should_reply:
            st.warning("Bot tidak akan membalas pesan ini karena:")
            st.markdown("- Ini pesan grup tanpa `@faq`")
            st.markdown("- Bot tidak di-mention")
            st.stop()
        
        # Step 2: Clean query
        clean_query = BotLogicService.clean_query(message)
        st.info(f"🔍 **Query bersih:** `{clean_query}`")
        
        # Step 3: Search (with mode selection)
        if local_search_mode in ("agent", "agent_pro"):
            use_pro = local_search_mode == "agent_pro"
            spinner_text = "🧠💎 Analisis mendalam dengan Pro..." if use_pro else "🧠 Menganalisis dengan LLM..."
            with st.spinner(spinner_text):
                start_time = time.time()
                result = AgentService.grade_search(clean_query, use_pro=use_pro)
                elapsed = time.time() - start_time
                results = [result] if result else []
            label = "Agent Pro" if use_pro else "Agent"
            st.success(f"⏱️ {label} mode took {elapsed:.2f}s")
        else:
            with st.spinner("⚡ Mencari di database..."):
                start_time = time.time()
                results = SearchService.search_for_bot(clean_query, top_n=BOT_TOP_RESULTS)
                elapsed = time.time() - start_time
            st.info(f"⏱️ Immediate mode took {elapsed:.2f}s")
        
        st.markdown("---")
        st.subheader("📥 Bot Response Preview")

        if not results:
            st.error("❌ Tidak ditemukan hasil yang relevan")
            st.markdown("""
            Bot akan mengirim pesan:
            > Maaf, saya tidak menemukan informasi terkait pertanyaan Anda.
            > Silakan hubungi Tim IT Support untuk bantuan lebih lanjut.
            """)
        else:
            # Show search results
            best = results[0]
            
            # Score badge
            score = best.score
            if score >= HIGH_RELEVANCE_THRESHOLD:
                score_badge = f"🌟 {score:.0f}%"
                score_color = "green"
            elif score >= MEDIUM_RELEVANCE_THRESHOLD:
                score_badge = f"✓ {score:.0f}%"
                score_color = "orange"
            else:
                score_badge = f"⚠️ {score:.0f}%"
                score_color = "red"
            
            st.markdown(f"**Relevansi:** :{score_color}[{score_badge}]")
            
            # Response card
            with st.container():
                st.markdown(f"### 📌 {best.judul}")
                st.markdown(f"**Tag:** `{best.tag}`")
                
                # Parse and display content
                jawaban = best.jawaban_tampil
                images_str = best.path_gambar
                
                # Check for images
                img_list = ContentParser.parse_image_paths(images_str)
                
                # Display text content
                st.markdown("---")
                
                # Clean content (remove [GAMBAR X] tags for preview)
                clean_content = jawaban
                for i in range(1, 10):
                    clean_content = clean_content.replace(f"[GAMBAR {i}]", "")
                clean_content = clean_content.strip()
                
                st.markdown(clean_content)
                
                # Display images
                if img_list:
                    st.markdown("---")
                    st.markdown("**📷 Gambar yang akan dikirim:**")
                    
                    cols = st.columns(min(3, len(img_list)))
                    for idx, img_path in enumerate(img_list):
                        fixed_path = ImageHandler.fix_path_for_ui(img_path)
                        with cols[idx % 3]:
                            if fixed_path and os.path.exists(fixed_path):
                                st.image(fixed_path, use_container_width=True)
                            else:
                                st.error(f"❌ File tidak ditemukan:\n{img_path}")
                
                # Source URL
                if best.sumber_url and len(best.sumber_url) > 3:
                    st.markdown("---")
                    st.markdown(f"🔗 **Sumber:** [{best.sumber_url}]({best.sumber_url})")
            
            # Show raw data for debugging
            with st.expander("🔧 Debug: Raw Data"):
                st.json({
                    "id": best.id,
                    "tag": best.tag,
                    "judul": best.judul,
                    "score": best.score,
                    "path_gambar": best.path_gambar,
                    "sumber_url": best.sumber_url
                })

st.markdown("---")
st.caption("💡 Tip: Bot tester memanggil SearchService langsung, tidak lewat webhook, jadi tidak ada error WPPConnect di terminal!")
