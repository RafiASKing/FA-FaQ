# Fast Cognitive Search System
Hospital's knowledge-base platform for SOPs, FAQs, and omnichannel support. It pairs semantic vector search (ChromaDB + Gemini embedding) with multi-surface delivery (Streamlit, FastAPI web, WhatsApp bot) and a safety-focused admin workflow.

---

## ✨ Highlight Features
| Area | Capability | References |
| --- | --- | --- |
| Core Search | Hybrid **Search Mode** (Top-3, score > 41%) & **Browse Mode** (10 latest, paginated). | [`app.py`](app.py), [`web_v2/main.py`](web_v2/main.py) |
| Vector DB | ChromaDB client-server fallback, HyDE-formatted embeddings, retry-on-lock wrapper. | [`src/database.py`](src/database.py) |
| Admin UX | Draft preservation, smart toolbar (`[GAMBAR X]` auto-counter), preview-before-publish, zombie image cleaner. | [`admin.py`](admin.py), [`src/utils.py`](src/utils.py) |
| Omnichannel | WhatsApp gateway with selective triggers, FastAPI webhook, media handling. | [`bot_wa.py`](bot_wa.py) |
| Configurability | Restricted tag palette + JSON source of truth, `.env`-driven AI thresholds and secrets. | [`src/utils.py`](src/utils.py), [`src/config.py`](src/config.py) |
| Analytics | Failed-search logging for content backlog insights. | [`src/utils.py`](src/utils.py), `data/failed_searches.csv` |

---

## 🗂️ Project Structure (partial)
```
.
├─ app.py                # Streamlit user app
├─ admin.py              # Streamlit admin console
├─ bot_wa.py             # FastAPI WhatsApp gateway
├─ web_v2/               # FastAPI + Jinja UI
├─ src/
│   ├─ config.py         # Env & path config
│   ├─ database.py       # Chroma access layer
│   └─ utils.py          # Tag/asset helpers
├─ data/
│   ├─ chroma_data/      # Persistent vector store (server mode)
│   ├─ tags_config.json  # Tag palette + descriptions
│   └─ failed_searches.csv
└─ images/               # Uploaded assets grouped per tag
```

---

## ⚙️ Setup

1. **Python deps**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Environment variables (`.env`)**
   ```ini
   GOOGLE_API_KEY=your_gemini_key
   ADMIN_PASSWORD=supersecret
   BOT_MIN_SCORE=80
   BOT_MIN_GAP=10
   WA_BASE_URL=http://wppconnect:21465
   WA_SESSION_KEY=THISISMYSECURETOKEN
   # Optional (auto-switch to Chroma server mode)
   CHROMA_HOST=chroma-server
   CHROMA_PORT=8000
   ```

3. **Initial tag palette**
   If `data/tags_config.json` is absent, the app seeds ED/OPD/IPD/Umum defaults. Edit via the admin console Config tab.

---

## 🚀 Running the Apps (local)

| Service | Command | Default Port |
| --- | --- | --- |
| User Streamlit | `streamlit run app.py --server.port 8501` | 8501 |
| Admin Streamlit | `streamlit run admin.py --server.port 8502` | 8502 |
| WhatsApp Bot API | `uvicorn bot_wa:app --host 0.0.0.0 --port 8000 --reload` | 8000 |
| Web V2 (FastAPI) | `uvicorn web_v2.main:app --host 0.0.0.0 --port 8080 --reload` | 8080 |

Static assets for Web V2 are served from `web_v2/static` and `/images` is mounted to expose uploaded media.

---

## 🐳 Docker / Compose

1. **Single container** (`Dockerfile`) exposes 8501/8502/8000. Override the default CMD via `docker compose`.
2. **Recommended multi-service layout** (see `Dokumentasi.md`): add a dedicated `chroma-server` service and mount `./data/chroma_data:/chroma/chroma`. Ensure every app service declares `depends_on: chroma-server`, shares the same network, and loads `.env`.

Restart steps after schema update / corruption recovery:
```bash
docker compose down
rm -rf data/faq_db
docker compose up --build -d
```

---

## 🧠 Search Logic Primer
1. **Embedding format** – HyDE template ensures consistent semantic signals:
   ```
   DOMAIN: {tag + desc}
   DOKUMEN: {judul}
   VARIASI PERTANYAAN USER: {keyword}
   ISI KONTEN: {cleaned answer}
   ```
2. **Two-phase retrieval**
   - Search Mode: `database.search_faq()` pre-filters by tag via Chroma `where`, applies score threshold, and keeps Top-3.
   - Browse Mode: `database.get_all_faqs_sorted()` streams newest 10 with pagination counters.
3. **Safety nets**
   - Confidence badges tinted by score bands (Streamlit + Web V2).
   - No-result CTA logs queries to `failed_searches.csv` and surfaces WhatsApp escalation.

---

## 🛠️ Admin Workflow Cheatsheet
1. **Drafting**
   - Use toolbar buttons in [`admin.py`](admin.py) to inject bold/list/`[GAMBAR X]`.
   - Upload images; they persist under `images/<TAG>/...` with sanitized filenames.
2. **Preview Mode**
   - Renders inline image placeholders exactly like the user app.
3. **Publishing**
   - Calls [`src/database.upsert_faq`](src/database.py) (auto ID, tag metadata enrichment, cached Gemini embedding).
4. **Edit/Delete**
   - Update form loads via cached DataFrame (`database.get_all_data_as_df`) and keeps destructive actions visually secondary.
   - Deletion cascades to filesystem via [`database.delete_faq`](src/database.py).

---

## 📱 WhatsApp Bot Notes
- Endpoint: `/webhook` in [`bot_wa.py`](bot_wa.py) expects payload from WPPConnect/Fonnte and triggers `process_logic`.
- Selective reply rules:
  - Always respond to private chats.
  - In groups, require `@faq`, mention, or trap keywords (“admin”, “tolong”, “tanya”, “help”).
- Media handling:
  - `[GAMBAR X]` tokens convert to inline captions; actual files sent asynchronously if stored.

---

## 🧰 Troubleshooting

| Issue | Symptom | Fix |
| --- | --- | --- |
| Vector DB desync (`chromadb.errors.InternalError: Error finding id`) | Searches fail after concurrent writes. | Restart services; if using embedded mode, migrate to server mode (see “Langkah 1-3” section in [`Dokumentasi.md`](Dokumentasi.md)). |
| SQLite lock / slow writes | Admin save stalls. | Ensure `retry_on_lock` decorator remains on write paths and avoid running admin/user containers against the same file backend. |
| Images missing in Web V2 | Broken `<img>` tags. | Confirm `/images` mount is configured and paths stored via `utils.save_uploaded_images`. |
| WhatsApp auth expired | `Bearer` token invalid. | Trigger `generate_token()` or restart bot service to refresh `CURRENT_TOKEN`. |

---

## 📎 Further Reading
- Full ADR & incident postmortem: [`Dokumentasi.md`](Dokumentasi.md)
- Palette & tag governance: [`data/tags_config.json`](data/tags_config.json)
- Sample combined script for LLM fine-tuning: [`single_script_for_llm.txt`](single_script_for_llm.txt)

Happy shipping! 🔧