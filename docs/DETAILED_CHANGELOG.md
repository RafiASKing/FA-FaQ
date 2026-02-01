# 📋 Detailed Changelog - FAQ Knowledge Base Refactoring

Dokumen ini berisi perubahan lengkap yang terjadi selama proses refactoring dari struktur flat ke struktur modular.

---

## 📊 Overview Perubahan

| Metric | Sebelum | Sesudah |
|--------|---------|---------|
| Files | 9 core files | 30+ modular files |
| Packages | 1 (`src/`) | 8 packages |
| Lines of Code | ~1,500 | ~2,800 |
| Code Duplication | Tinggi | Minimal |
| Test Coverage | 0% | Basic tests added |

---

## 🗂️ Struktur Directory Baru

```
eighthExperiment/
├── config/                    # 📌 NEW: Configuration Layer
│   ├── __init__.py
│   ├── settings.py            # Pydantic BaseSettings
│   ├── constants.py           # Magic numbers centralized
│   └── database.py            # DatabaseFactory class
│
├── core/                      # 📌 NEW: Core Utilities
│   ├── __init__.py
│   ├── content_parser.py      # Unified [GAMBAR X] parser
│   ├── image_handler.py       # Image operations
│   ├── tag_manager.py         # Tag config management
│   └── logger.py              # Logging utilities
│
├── app/                       # 📌 NEW: Application Layer
│   ├── __init__.py
│   ├── Kernel.py              # FastAPI app factory
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   ├── embedding_service.py
│   │   ├── search_service.py
│   │   ├── faq_service.py
│   │   └── whatsapp_service.py
│   ├── schemas/               # Pydantic models
│   │   ├── __init__.py
│   │   ├── faq_schema.py
│   │   ├── search_schema.py
│   │   └── webhook_schema.py
│   └── controllers/           # FastAPI routers
│       ├── __init__.py
│       ├── search_controller.py
│       ├── faq_controller.py
│       └── webhook_controller.py
│
├── routes/                    # 📌 NEW: Route Aggregation
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1.py
│   └── web.py
│
├── streamlit_apps/            # 📌 NEW: Streamlit Applications
│   ├── __init__.py
│   ├── user_app.py            # Migrated from app.py
│   └── admin_app.py           # Migrated from admin.py
│
├── sandbox/                   # 📌 NEW: Experimental Features
│   ├── __init__.py
│   └── llm_grader.py          # Placeholder for future LLM agent
│
├── tests/                     # 📌 NEW: Test Suite
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_core.py
│   └── test_services.py
│
├── main.py                    # 📌 NEW: Entry point
├── pytest.ini                 # 📌 NEW: Test configuration
│
├── src/                       # 🔄 PRESERVED: Original code (backward compatible)
├── web_v2/                    # 🔄 PRESERVED: Templates & static files
├── app.py                     # 🔄 PRESERVED: Original user app
├── admin.py                   # 🔄 PRESERVED: Original admin app
└── bot_wa.py                  # 🔄 PRESERVED: Original bot
```

---

## 📝 File-by-File Changelog

### 1. Configuration Layer (`config/`)

#### `config/settings.py`
**Source:** `src/config.py` (partial)

| Original | New |
|----------|-----|
| `GOOGLE_API_KEY = os.getenv(...)` | `google_api_key: str = Field(..., alias="GOOGLE_API_KEY")` |
| `ADMIN_PASSWORD_HASH = os.getenv(...)` | `admin_password_hash: str = Field(...)` |
| `BOT_MIN_SCORE = float(os.getenv(...))` | `bot_min_score: float = Field(default=80.0)` |
| `BOT_MIN_GAP = float(os.getenv(...))` | `bot_min_gap: float = Field(default=10.0)` |
| `BASE_DIR = os.path.dirname(...)` | `PathSettings.BASE_DIR = Path(__file__).parent.parent` |

**Improvements:**
- Type validation via Pydantic
- Default values dengan Field
- Single source of truth untuk semua env vars
- `PathSettings` class untuk path management
- Auto directory creation

#### `config/constants.py`
**Source:** Magic numbers dari berbagai files

| Constant | Value | Original Location |
|----------|-------|-------------------|
| `RELEVANCE_THRESHOLD` | 41 | `app.py` line ~145 |
| `HIGH_RELEVANCE_THRESHOLD` | 80 | `app.py` line ~223 |
| `MEDIUM_RELEVANCE_THRESHOLD` | 50 | `app.py` line ~227 |
| `ITEMS_PER_PAGE` | 10 | `app.py` line ~163 |
| `BOT_TOP_RESULTS` | 5 | `bot_wa.py` line ~161 |
| `WEB_TOP_RESULTS` | 3 | `app.py` line ~152 |
| `IMAGE_MAX_WIDTH` | 1024 | `src/utils.py` line ~56 |
| `IMAGE_QUALITY` | 70 | `src/utils.py` line ~57 |
| `MAX_RETRIES` | 10 | `src/database.py` line ~23 |
| `COLLECTION_NAME` | "faq_universal_v1" | `src/config.py` line ~18 |
| `HEX_TO_STREAMLIT_COLOR` | {...} | `app.py` line ~40-48 |
| `COLOR_PALETTE` | {...} | `src/utils.py` line ~12-19 |

#### `config/database.py`
**Source:** `src/database.py` (partial)

**Changes:**
- `_get_db_client_raw()` → `DatabaseFactory.get_db_client()`
- `_get_ai_client_raw()` → `DatabaseFactory.get_ai_client()`
- `get_collection()` → `DatabaseFactory.get_collection()`
- Added `DatabaseFactory.reset_clients()` for testing
- Singleton pattern dengan class variables
- Removed Streamlit cache dependency (untuk reusability)

---

### 2. Core Utilities (`core/`)

#### `core/content_parser.py`
**Source:** 4 implementasi berbeda yang di-unify

| Feature | Original Locations |
|---------|-------------------|
| Parse `[GAMBAR X]` | `app.py`, `admin.py`, `bot_wa.py`, `web_v2/main.py` |
| Clean for embedding | `src/utils.py:clean_text_for_embedding()` |
| Fix markdown format | `web_v2/main.py:fix_markdown_format()` |

**New Methods:**
```python
ContentParser.parse_image_paths(path_string) -> List[str]
ContentParser.clean_for_embedding(text) -> str
ContentParser.count_image_tags(text) -> int
ContentParser.to_html(text, image_paths) -> str
ContentParser.to_whatsapp(text, image_paths) -> Tuple[str, List]
ContentParser.get_streamlit_parts(text, image_paths) -> List[dict]
```

**Improvements:**
- Single regex pattern `IMAGE_TAG_PATTERN`
- Format-specific output methods
- Consistent error handling

#### `core/image_handler.py`
**Source:** `src/utils.py` (image functions)

| Original | New |
|----------|-----|
| `sanitize_filename(text)` | `ImageHandler.sanitize_filename(text)` |
| `save_uploaded_images(...)` | `ImageHandler.save_uploaded_images(...)` |
| `fix_image_path_for_ui(db_path)` | `ImageHandler.fix_path_for_ui(db_path)` |
| `get_base64_image(file_path)` | `ImageHandler.get_base64_image(file_path)` |

**New Methods:**
```python
ImageHandler.delete_images(path_string) -> List[str]
ImageHandler.check_image_exists(path) -> bool
```

#### `core/tag_manager.py`
**Source:** `src/utils.py` (tag functions)

| Original | New |
|----------|-----|
| `load_tags_config()` | `TagManager.load_tags()` |
| `save_tags_config(tags_dict)` | `TagManager.save_tags(tags_dict)` |
| - | `TagManager.get_tag_color(tag_name)` |
| - | `TagManager.get_tag_description(tag_name)` |
| - | `TagManager.get_streamlit_color_name(tag_name)` |
| - | `TagManager.hex_to_streamlit_color(hex_code)` |
| - | `TagManager.add_tag(name, color, desc)` |
| - | `TagManager.delete_tag(name)` |

**Improvements:**
- File-based caching dengan mtime check
- Singleton pattern
- Type hints

#### `core/logger.py`
**Source:** `src/utils.py:log_failed_search()` + scattered `print()` calls

**New Functions:**
```python
log(message, flush=True)           # Timestamped logging
log_failed_search(query) -> bool   # CSV logging
clear_failed_search_log() -> bool  # Clear log file
LoggerMixin                        # Mixin class for classes
```

---

### 3. Application Layer (`app/`)

#### `app/services/embedding_service.py`
**Source:** `src/database.py` (embedding functions)

| Original | New |
|----------|-----|
| `_generate_embedding_raw(text)` | `EmbeddingService.generate_embedding(text)` |
| `generate_embedding_cached(text)` | `EmbeddingService.generate_query_embedding(query)` |
| - | `EmbeddingService.generate_faq_embedding(...)` |

**Improvements:**
- HyDE format generation built-in
- Decoupled from Streamlit cache
- Retry decorator with jitter backoff

#### `app/services/search_service.py`
**Source:** `src/database.py` (search functions)

| Original | New |
|----------|-----|
| `search_faq(query, filter_tag, n_results)` | `SearchService.search(query, filter_tag, n_results, min_score)` |
| `search_faq_for_bot(query, filter_tag)` | `SearchService.search_for_bot(query, filter_tag)` |
| `get_all_faqs_sorted()` | `SearchService.get_all_faqs(filter_tag)` |
| `get_unique_tags_from_db()` | `SearchService.get_unique_tags()` |
| Manual score calculation | `SearchService.calculate_relevance(distance)` |
| Manual score class | `SearchService.get_score_class(score)` |

**New Features:**
- `SearchResult` dataclass
- Pre-filtering by tag in query
- Threshold filtering built-in

#### `app/services/faq_service.py`
**Source:** `src/database.py` (CRUD functions)

| Original | New |
|----------|-----|
| `upsert_faq(...)` | `FaqService.upsert(...)` |
| `delete_faq(doc_id)` | `FaqService.delete(doc_id)` |
| `get_all_data_as_df()` | `FaqService.get_all_as_dataframe()` |
| - | `FaqService.get_by_id(doc_id)` |
| - | `FaqService.count_by_tag(tag)` |

**Improvements:**
- Cascade delete dengan image cleanup
- Auto ID generation
- Decoupled from Streamlit cache

#### `app/services/whatsapp_service.py`
**Source:** `bot_wa.py` (WhatsApp functions)

| Original | New |
|----------|-----|
| `get_headers()` | `WhatsAppService.get_headers()` |
| `generate_token()` | `WhatsAppService.generate_token()` |
| `send_wpp_text(phone, message)` | `WhatsAppService.send_text(phone, message)` |
| `send_wpp_image(phone, file_path, caption)` | `WhatsAppService.send_image(phone, file_path, caption)` |
| - | `WhatsAppService.send_images(phone, file_paths, delay)` |
| - | `WhatsAppService.should_reply_to_message(...)` |
| - | `WhatsAppService.clean_query(message_body)` |

---

### 4. Schemas (`app/schemas/`)

**New Files:**
- `faq_schema.py`: `FaqCreate`, `FaqUpdate`, `FaqResponse`, `FaqListResponse`
- `search_schema.py`: `SearchRequest`, `SearchResponse`, `SearchResultItem`
- `webhook_schema.py`: `WhatsAppWebhookPayload`, `WebhookResponse`

**Features:**
- Pydantic models untuk validation
- Type hints
- Helper methods di webhook schema

---

### 5. Controllers (`app/controllers/`)

**New Files:**
- `search_controller.py`: `/search` endpoints
- `faq_controller.py`: `/faq` CRUD endpoints
- `webhook_controller.py`: WhatsApp webhook handler

**Features:**
- FastAPI APIRouter
- Background task processing
- Proper HTTP status codes

---

### 6. Routes (`routes/`)

**New Files:**
- `routes/api/v1.py`: Aggregates all API controllers
- `routes/web.py`: HTML template routes (migrated from `web_v2/main.py`)

---

### 7. Streamlit Apps (`streamlit_apps/`)

#### `streamlit_apps/user_app.py`
**Source:** `app.py` (274 lines)

**Changes:**
- Uses `SearchService` instead of direct database calls
- Uses `TagManager` for tag operations
- Uses `ContentParser` for content rendering
- Uses `constants.py` for magic numbers
- Uses `settings.wa_support_number` for WhatsApp CTA

**Preserved:**
- All UI layout
- Pagination logic
- Score badge coloring
- Mixed content rendering
- WhatsApp CTA button

#### `streamlit_apps/admin_app.py`
**Source:** `admin.py` (416 lines)

**Changes:**
- Uses `FaqService` for CRUD operations
- Uses `TagManager` for tag config
- Uses `ImageHandler` for image operations
- Uses `ContentParser.count_image_tags()` for smart editor
- Uses `clear_failed_search_log()` from logger

**Preserved:**
- All 5 tabs (Database, New FAQ, Edit/Delete, Config Tags, Analytics)
- Preview mode
- Smart editor with image tag auto-increment
- Backup/Restore feature

---

### 8. Entry Points

#### `main.py`
**NEW FILE**

```python
# Pre-create app instances untuk uvicorn
api_app = create_api_app()
bot_app = create_bot_app()
web_app = create_web_app()

# CLI interface
if __name__ == "__main__":
    # python main.py api|bot|web
```

#### `app/Kernel.py`
**NEW FILE**

Factory pattern untuk FastAPI apps:
```python
create_api_app() -> FastAPI    # For API endpoints
create_bot_app() -> FastAPI    # For WhatsApp bot
create_web_app() -> FastAPI    # For Web V2 HTML
```

---

### 9. Updated Files

#### `docker-compose.yml`
**Changes:**
```yaml
# Old
command: streamlit run app.py
command: streamlit run admin.py
command: uvicorn bot_wa:app
command: uvicorn web_v2.main:app

# New
command: streamlit run streamlit_apps/user_app.py
command: streamlit run streamlit_apps/admin_app.py
command: uvicorn main:bot_app
command: uvicorn main:web_app
```

#### `requirements.txt`
**Added:**
- `pydantic-settings` - untuk Pydantic BaseSettings
- `pytest` - untuk testing

---

### 10. Sandbox & Tests

#### `sandbox/llm_grader.py`
**NEW FILE** - Placeholder untuk future LLM Agent Grader

**Classes:**
- `GradeResult` dataclass
- `BaseLLMGrader` abstract class
- `PlaceholderGrader` implementation
- `get_grader(provider)` factory function

#### `tests/`
**NEW FILES**
- `test_config.py` - Test settings dan constants
- `test_core.py` - Test ContentParser dan TagManager
- `test_services.py` - Test SearchService dan FaqService

---

## 🔧 Fixes Applied During Review

1. **Test file bug:** `ContentParser` was being used as instance instead of classmethod
2. **Missing method:** Added `TagManager.hex_to_streamlit_color()` method
3. **Export missing:** Added `clear_failed_search_log` to `core/__init__.py` exports

---

## ⚠️ Breaking Changes

**None** - Backward compatibility maintained:
- Original files (`app.py`, `admin.py`, `bot_wa.py`, `src/`) still work
- Docker commands updated but old commands still function

---

## 🚀 Migration Guide

### Gradual Migration
1. Update `docker-compose.yml` satu service pada satu waktu
2. Test setiap service sebelum lanjut
3. Monitor logs untuk error

### Full Migration
```bash
# 1. Update docker-compose.yml ke path baru
# 2. Rebuild containers
docker-compose build
docker-compose up -d

# 3. Test semua endpoints
curl http://localhost:8000/health
curl http://localhost:8080/
# Browser: http://localhost:8501, http://localhost:8502
```

---

## 📈 Benefits

1. **Maintainability:** Single responsibility per file
2. **Testability:** Services dapat di-mock dan di-test
3. **Reusability:** Core utilities dapat dipakai berbagai tempat
4. **Scalability:** Easy to add new features
5. **Documentation:** Type hints dan docstrings
6. **Configuration:** Centralized settings management
7. **Future-ready:** Placeholder untuk LLM agent sudah ada
