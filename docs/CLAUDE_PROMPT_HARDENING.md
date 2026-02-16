# Role: Senior Python Backend Engineer (Siloam AI Team)

## Context
You are working on **FA-FaQ**, a hospital FAQ system using **FastAPI + Typesense + LangChain + Gemini**.
The system uses a strict **Ports & Adapters (Hexagonal)** architecture.
- **Controllers** handle HTTP/Webhooks.
- **Services** contain business logic.
- **Ports** are abstract interfaces.
- **Adapters** are concrete implementations (Typesense, Gemini, WPPConnect).

## Objective
Your task is to **harden** the codebase for production pilot.
You must implement **3 specific improvements** without breaking existing logic.

---

## Task 1: Robust Error Handling
**Goal**: Replace generic `500 Internal Server Error` with sanitized JSON responses.
1.  **Create Exception Classes** in `core/exceptions.py`:
    - `AppError` (Base class)
    - `SearchError` (for vector DB or LLM failures)
    - `AuthError` (for missing API keys)
    - `RateLimitError` (already handled by slowapi, but ensure consistency)
2.  **Update Controllers**:
    - Wrap logic in `try/except` blocks.
    - Catch specific errors and raise `HTTPException` with **sanitized messages** (e.g., "Search service unavailable (Ref: ERR-123)" instead of raw stack trace).
    - **Log the full stack trace** using `core.logger.log_error()` before returning the sanitized error.

---

## Task 2: API Key Authentication
**Goal**: Protect the public `/search` endpoints from unauthorized access.
1.  **Configuration**:
    - Add `API_KEY` to `config/settings.py` (load from env var `APP_API_KEY`).
2.  **Security Dependency**:
    - Create `app/dependencies/auth.py`.
    - Implement a `verify_api_key` dependency that checks the `X-API-Key` header.
3.  **Apply to Routes**:
    - Apply this dependency to `app/controllers/search_controller.py`.
    - **Exception**: Do NOT apply to `webhook_controller.py` (it uses `X-Webhook-Secret` signature validation instead).

---

## Task 3: Comprehensive Unit Testing
**Goal**: Increase test coverage from 5% to ~60%.
1.  **Framework**: Use `pytest`.
2.  **Create Tests**:
    - `tests/test_services/test_search_service.py`: Test relevance logic, filtering, and empty results.
    - `tests/test_services/test_faq_service.py`: Test CRUD, ID generation, and module verification.
    - `tests/test_core/test_group_config.py`: Test whitelist logic (allow/deny modules).
3.  **Mocking**:
    - **IMPORTANT**: Do NOT call real Gemini API or Typesense.
    - Mock the `VectorStorePort` and `LLMPort` using `unittest.mock` or `pytest-mock`.
    - We want to test the *Service Logic*, not the external APIs.

---

## Constraints
1.  **Do NOT change the architecture.** Keep code in `app/services`, `app/controllers`, etc.
2.  **Use existing Logger.** Import `from core.logger import log` or `_logger`.
3.  **Type Hints.** Ensure all new code has Python type hints.

## Deliverables
Please provide the code for:
1.  `core/exceptions.py`
2.  `app/dependencies/auth.py`
3.  Updated `search_controller.py`
4.  New test files in `tests/`
