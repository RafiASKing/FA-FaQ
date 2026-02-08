# Refactoring V2.3: Typesense Migration

**Date**: 2026-02-08  
**Status**: ✅ Complete

---

## Overview

Migrated vector database from **ChromaDB** to **Typesense** (Siloam standard). This improves reliability, removes SQLite locking issues, and aligns with production standards.

## Why Typesense?

| Issue | ChromaDB | Typesense |
|-------|----------|-----------|
| **Concurrency** | SQLite locks, needs retry logic | Native multi-threaded |
| **Memory** | Embedded mode leaks memory | Production-grade efficiency |
| **Search** | Good for local dev | Better REST API, multi_search |
| **Siloam Standard** | ❌ | ✅ |

---

## Changes Made

### New Files
| File | Description |
|------|-------------|
| `config/typesenseDb.py` | TypesenseVectorStoreAdapter implementing VectorStorePort |

### Deleted Files
| File | Reason |
|------|--------|
| `config/chromaDb.py` | Replaced by Typesense |
| `scripts/migrate_chroma_to_typesense.py` | One-time migration done |
| `tests/test_search_methods.py` | Legacy ChromaDB test |

### Modified Files

#### `config/settings.py`
```diff
- vector_db: str = Field(default="typesense", alias="VECTOR_DB")
- chroma_host: str | None = Field(...)
- chroma_port: int | None = Field(...)
+ typesense_host: str = Field(default="localhost", alias="TYPESENSE_HOST")
+ typesense_port: int = Field(default=8118, alias="TYPESENSE_PORT")
+ typesense_api_key: str = Field(default="xyz", alias="TYPESENSE_API_KEY")
+ typesense_collection: str = Field(default="hospital_faq_kb", alias="TYPESENSE_COLLECTION")
```

#### `config/container.py`
```diff
- if settings.use_typesense:
-     # Typesense (default)
-     ...
- else:
-     # ChromaDB (fallback)
-     from config.chromaDb import ChromaDBVectorStoreAdapter
-     ...
+ _vector_store = TypesenseVectorStoreAdapter(
+     host=settings.typesense_host,
+     port=settings.typesense_port,
+     api_key=settings.typesense_api_key,
+     collection_name=settings.typesense_collection,
+     embedding_dim=EMBEDDING_DIMENSION,
+ )
```

#### `config/constants.py`
```diff
- COLLECTION_NAME = "faq_universal_v1"  # ChromaDB legacy
- MAX_RETRIES = 10                      # For database lock retry
- RETRY_BASE_DELAY = 0.1
+ EMBEDDING_DIMENSION = 3072            # gemini-embedding-001
```

#### `docker-compose.yml`
```diff
- # --- CHROMA DB (fallback) ---
- chroma-server:
-   image: chromadb/chroma:latest
-   ...
+ # --- TYPESENSE ---
+ typesense:
+   image: typesense/typesense:27.1
+   ports:
+     - "8118:8108"
+   environment:
+     - TYPESENSE_API_KEY=xyz
```

#### `requirements.txt`
```diff
- chromadb==1.3.4
- pysqlite3-binary; sys_platform == 'linux'
+ typesense
```

---

## Technical Notes

### Embedding Dimension
- **Model**: `gemini-embedding-001`
- **Dimension**: 3072 (not 768!)
- Important for Typesense schema creation

### Port Configuration
- **External (Windows/Host)**: `8118`
- **Internal (Docker network)**: `8108`
- This avoids conflict with other Typesense instances

### Multi-Search API
Large embedding vectors (3072 floats) exceed URL length limits. Fixed by using:
```python
response = self._client.multi_search.perform(
    search_request,
    {"vector_query": f"embedding:([{...}], k:{n_results})"}
)
```

---

## Environment Variables

### Required
```ini
TYPESENSE_HOST=localhost      # or "typesense" in Docker
TYPESENSE_PORT=8118           # or 8108 for container-to-container
TYPESENSE_API_KEY=xyz
TYPESENSE_COLLECTION=hospital_faq_kb
```

### Removed
```ini
# No longer needed:
VECTOR_DB=...
CHROMA_HOST=...
CHROMA_PORT=...
```

---

## Migration Steps (Historical)

1. Created Typesense collection with 3072-dim schema
2. Ran migration script to transfer 28 documents
3. Re-generated embeddings using Gemini API
4. Verified search works correctly
5. Removed ChromaDB code and dependencies

---

## Deployment

### Local Dev (Windows)
```powershell
docker compose up typesense -d
pip install typesense
python main.py api --port 8001
```

### Production (Lightsail)
```bash
docker compose up --build -d typesense faq-web-v2 faq-admin faq-user faq-bot wppconnect
```

---

## RAM Impact

| Component | Before (ChromaDB) | After (Typesense) |
|-----------|-------------------|-------------------|
| Vector DB | ~300-500 MB | ~50-100 MB |
| SQLite Overhead | Yes | No |
| Total (2GB Lightsail) | ⚠️ Tight | ✅ Comfortable |

---

# V2.3.1 Updates (2026-02-08)

## 1. Embedding Template Centralization

### Problem
Template for embedding documents (`MODUL`, `TOPIK`, `TERKAIT`, `ISI KONTEN`) was duplicated in multiple places.

### Solution
Centralized template in `EmbeddingService`:

```python
# app/services/embedding_service.py
class EmbeddingService:
    @classmethod
    def _build_document_text(cls, tag, judul, jawaban, keywords) -> str:
        """Single source of truth for embedding template."""
        return f"""MODUL: {tag} ({tag_desc})
TOPIK: {judul}
TERKAIT: {keywords}
ISI KONTEN: {clean_jawaban}"""

    @classmethod
    def build_faq_document(cls, tag, judul, jawaban, keywords) -> tuple[List[float], str]:
        """Returns (embedding_vector, document_text)"""
        text = cls._build_document_text(...)
        return container.get_embedding().embed(text), text
```

### Files Modified
| File | Change |
|------|--------|
| `app/services/embedding_service.py` | Added `_build_document_text()`, `build_faq_document()` |
| `app/services/faq_service.py` | Now uses `EmbeddingService.build_faq_document()` |
| `scripts/reembed_all.py` | Now uses `EmbeddingService.build_faq_document()` |

---

## 2. Group Module Whitelist

### Feature
Per-group module filtering for WhatsApp bot. Each group can be configured to only search specific modules.

### Design
- **Auto-registration**: Groups auto-register on first @faq mention
- **Default**: All modules allowed
- **DM (Private)**: Always all modules
- **Admin UI**: New tab in admin console

### Files Created/Modified
| File | Change |
|------|--------|
| `data/group_config.json` | NEW - JSON storage |
| `core/group_config.py` | NEW - GroupConfig service |
| `app/services/search_service.py` | Added `allowed_modules` parameter |
| `app/controllers/webhook_controller.py` | Added group detection + auto-register |
| `app/schemas/webhook_schema.py` | Added `get_group_name()` |
| `streamlit_apps/admin_app.py` | Added **🏢 Group Settings** tab |

### Data Structure
```json
{
  "groups": {
    "6281xxx@g.us": {
      "name": "EMR ED - SHKJ",
      "allowed_modules": ["EMR ED"],
      "first_seen": "2026-02-08T19:00:00"
    }
  }
}
```

### Flow
```
1. WA message from group → Check if registered
2. If new → Auto-register with default "all"
3. Get allowed_modules for group
4. Filter search results by those modules
5. Return filtered response
```

---

## 3. WPPConnect API Enhancement

### Problem
Group name might not be in webhook payload, making admin UI confusing.

### Solution
Fetch group name from WPPConnect API with fallback chain:

```
1. Check payload.get_group_name()
2. If empty → Call messaging.get_group_name(group_id)
3. If fails → Use "Group {jid[:20]}..."
```

### Files Modified
| File | Change |
|------|--------|
| `config/messaging.py` | Added `get_chat_info()`, `get_group_name()` |
| `app/controllers/webhook_controller.py` | Enhanced group name resolution |

---

## Next: Agent Mode

### Current State
Agent mode scaffolding already exists:
- `app/services/agent_service.py` — LLM reranking
- `app/services/agent_prompts.py` — Prompt templates
- `app/schemas/agent_schema.py` — RerankOutput schema
- `/api/v1/agent/rerank` — API endpoint

### Pending
- Mode switch in admin (global or per-group)
- Webhook integration to call AgentService
- Testing via WhatsApp
