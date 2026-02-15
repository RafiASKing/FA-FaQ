"""Verification script for pre-production hardening."""

# Test all imports
from config.settings import settings, paths
from config.middleware import setup_middleware
from config.constants import RELEVANCE_THRESHOLD, HIGH_RELEVANCE_THRESHOLD, MEDIUM_RELEVANCE_THRESHOLD, AGENT_MIN_SCORE
from core.logger import log, log_search, log_failed_search, clear_search_log, get_search_log_path, clear_failed_search_log
from core import log_search, clear_search_log, get_search_log_path
from app.controllers.webhook_controller import WebhookController
from app.controllers.agent_controller import agentController
from app.services.agent_service import AgentService
from app.services.search_service import SearchService
from app.services.faq_service import FaqService
from routes.web import router

# Verify configurations
print("=== Config OK ===")
print("CORS:", settings.cors_origins_list)
ws = "SET" if settings.webhook_secret else "NOT SET (dev mode)"
print("Webhook secret:", ws)
print("Templates:", paths.TEMPLATES_DIR, "exists=", paths.TEMPLATES_DIR.exists())
print("Static:", paths.STATIC_DIR, "exists=", paths.STATIC_DIR.exists())
print("Thresholds: REL=%s HIGH=%s MED=%s" % (RELEVANCE_THRESHOLD, HIGH_RELEVANCE_THRESHOLD, MEDIUM_RELEVANCE_THRESHOLD))
print("Agent min score:", AGENT_MIN_SCORE)
print("Search log path:", get_search_log_path())

# Verify no DB_PATH
assert not hasattr(paths, 'DB_PATH'), "DB_PATH should be removed!"
print("DB_PATH removed: OK")

# Verify no rerank_search
assert not hasattr(AgentService, 'rerank_search'), "rerank_search should be removed!"
print("rerank_search removed: OK")

# Test log_search
import os
ok = log_search("test query", score=85.5, faq_id="test123", faq_title="Test FAQ", mode="immediate", response_ms=150, source="test")
print("log_search works:", ok)

# Cleanup test
log_path = get_search_log_path()
if log_path.exists():
    os.remove(log_path)

print()
print("=== ALL VERIFICATION PASSED ===")
