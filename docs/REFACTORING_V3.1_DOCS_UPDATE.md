# v3.1 Docs Update — Documentation Alignment

> **Date**: 2026-02-16
> **Type**: Documentation + Validation Update
> **Previous Runtime Release**: v3.0

---

## Summary

v3.1 is a **documentation refresh release** to align project docs with the current runtime behavior and recent hardening work.

No architecture migration is introduced in this release; focus is consistency and operational clarity.

---

## What Was Updated

### 1) README Modernization
- Updated runtime narrative from older references to current **Typesense-first** system
- Added Windows-friendly local flow (partial Docker stack + bot tester)
- Added `APP_API_KEY` guidance for `/api/v1/*` security
- Added latest test validation snapshot

### 2) System Overview Refresh
- Version bumped to **3.1 (Docs Update)**
- Added explicit section for v3.1 scope
- Added API hardening references:
  - `app/dependencies/auth.py`
  - `routes/api/v1.py`
  - `app/controllers/search_controller.py`
  - `core/exceptions.py`
  - `core/logger.py`
- Clarified local Windows flow and container healthcheck caveat

### 3) Memory Refresh
- Version bumped to **v3.1**
- Added fast pointers for API security, sanitized errors, and test state
- Added current gotchas for Windows local setup and compose healthcheck behavior

### 4) Compose Healthcheck Fix
- Updated `docker-compose.yml` with per-service healthchecks:
  - `faq-bot` -> `localhost:8000/health`
  - `faq-web-v2` -> `localhost:8080/`
  - `faq-user` -> `localhost:8501/`
  - `faq-admin` -> `localhost:8502/`
- Purpose: prevent false `unhealthy` status on web/user/admin containers caused by inherited default healthcheck to port 8000.

---

## Runtime/Code Context Captured in Docs

- API key uses `APP_API_KEY` (legacy fallback `API_KEY`)
- Search controller now returns sanitized error details with reference code
- Internal traceback logging is captured through `log_error()`
- Current local test status: **29 passed**

---

## Notes

- v3.0 remains the last production deployment/migration release
- v3.1 is intentionally marked as docs alignment to keep release history clear
