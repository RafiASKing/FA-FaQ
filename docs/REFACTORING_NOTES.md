# Struktur Baru - FAQ Knowledge Base

## Refactoring Summary
Project ini telah di-refactor dari struktur flat menjadi struktur modular mengikuti prinsip Siloam Workspace Template.

## New Directory Structure

```
eighthExperiment/
├── config/                          # Configuration Layer
│   ├── __init__.py                  # Exports settings, paths, constants
│   ├── settings.py                  # Pydantic BaseSettings (env vars)
│   ├── constants.py                 # Magic numbers centralized
│   └── database.py                  # DatabaseFactory (ChromaDB)
│
├── core/                            # Core Utilities
│   ├── __init__.py
│   ├── content_parser.py            # Unified [GAMBAR X] parser
│   ├── image_handler.py             # Image save/delete/base64
│   ├── tag_manager.py               # Tag config JSON management
│   └── logger.py                    # Logging utilities
│
├── app/                             # Application Layer
│   ├── __init__.py
│   ├── Kernel.py                    # FastAPI app factory
│   │
│   ├── services/                    # Business Logic
│   │   ├── __init__.py
│   │   ├── embedding_service.py     # Google Gemini embedding
│   │   ├── search_service.py        # Semantic search operations
│   │   ├── faq_service.py           # FAQ CRUD operations
│   │   └── whatsapp_service.py      # WPPConnect integration
│   │
│   ├── schemas/                     # Pydantic Models
│   │   ├── __init__.py
│   │   ├── faq_schema.py            # FAQ request/response models
│   │   ├── search_schema.py         # Search request/response models
│   │   └── webhook_schema.py        # WhatsApp webhook models
│   │
│   └── controllers/                 # FastAPI Routers
│       ├── __init__.py
│       ├── search_controller.py     # /search endpoints
│       ├── faq_controller.py        # /faq CRUD endpoints
│       └── webhook_controller.py    # WhatsApp webhook handler
│
├── routes/                          # Route Aggregation
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1.py                    # API v1 routes
│   └── web.py                       # HTML template routes
│
├── streamlit_apps/                  # Streamlit Applications
│   ├── __init__.py
│   ├── user_app.py                  # User search interface
│   └── admin_app.py                 # Admin console
│
├── sandbox/                         # Experimental Features
│   ├── __init__.py
│   └── llm_grader.py                # LLM Agent Grader (placeholder)
│
├── tests/                           # Test Suite
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_core.py
│   └── test_services.py
│
├── web_v2/                          # Static files for web frontend
│   ├── static/
│   └── templates/
│
├── main.py                          # Entry point (api, bot, web)
├── docker-compose.yml               # Updated paths
├── requirements.txt                 # Added pydantic-settings, pytest
└── pytest.ini                       # Test configuration
```

## Key Improvements

### 1. Configuration Layer
- **Before:** Magic numbers scattered, env vars accessed directly
- **After:** Centralized in `config/settings.py` (Pydantic) and `config/constants.py`

### 2. Service Layer
- **Before:** Business logic mixed in UI code
- **After:** Clean separation in `app/services/`

### 3. Content Parsing
- **Before:** 4 different implementations of `[GAMBAR X]` parsing
- **After:** Unified `ContentParser` with format-specific outputs

### 4. Database Access
- **Before:** Direct ChromaDB calls everywhere
- **After:** `DatabaseFactory` pattern with auto server/local detection

### 5. Entry Points
- **Before:** Separate files for each app
- **After:** Single `main.py` with CLI commands

## Docker Commands (Updated)

```bash
# Bot WhatsApp
uvicorn main:bot_app --host 0.0.0.0 --port 8000

# Web V2
uvicorn main:web_app --host 0.0.0.0 --port 8080

# User App (Streamlit)
streamlit run streamlit_apps/user_app.py --server.port=8501

# Admin App (Streamlit)
streamlit run streamlit_apps/admin_app.py --server.port=8502
```

## Backward Compatibility

Original files are **still present** and will continue to work:
- `app.py` → Original user app
- `admin.py` → Original admin app
- `bot_wa.py` → Original WhatsApp bot
- `web_v2/main.py` → Original web frontend
- `src/` → Original utilities

You can gradually migrate by updating `docker-compose.yml` to use new paths.

## Future: LLM Grader Agent

Placeholder sudah dibuat di `sandbox/llm_grader.py` dengan:
- `BaseLLMGrader` abstract class
- `GradeResult` dataclass
- `PlaceholderGrader` implementation
- Factory function `get_grader()`

Untuk implementasi actual, extend `BaseLLMGrader` dengan provider seperti Gemini/OpenAI.
