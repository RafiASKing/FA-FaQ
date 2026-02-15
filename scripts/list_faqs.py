"""List all FAQ titles from the database."""
from app.services.search_service import SearchService

faqs = SearchService.get_all_faqs()
print(f"Total FAQs: {len(faqs)}")
print("=" * 60)
for f in faqs:
    tag = f.get("tag", "?")
    judul = f.get("judul", "?")
    keywords = f.get("keywords_raw", "")
    print(f"[{tag}] {judul}")
    if keywords:
        print(f"    keywords: {keywords[:80]}")
