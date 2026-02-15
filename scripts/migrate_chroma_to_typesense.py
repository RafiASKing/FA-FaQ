"""
Migration Script: ChromaDB → Typesense

Usage:
  STEP 1 (on old server, with ChromaDB still running):
    python scripts/migrate_chroma_to_typesense.py export

  STEP 2 (after new code deployed, with Typesense running):
    python scripts/migrate_chroma_to_typesense.py import
"""

import json
import os
import sys

EXPORT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "migration_export.json")


def export_from_chroma():
    """Export all FAQs from ChromaDB to a JSON file."""
    import chromadb

    host = os.getenv("CHROMA_HOST", "localhost")
    port = int(os.getenv("CHROMA_PORT", "8000"))

    print(f"Connecting to ChromaDB at {host}:{port}...")
    client = chromadb.HttpClient(host=host, port=port)
    collection = client.get_or_create_collection(name="faq_universal_v1")

    data = collection.get(include=["metadatas", "documents"])

    if not data["ids"]:
        print("No data found in ChromaDB!")
        return

    faqs = []
    for i, doc_id in enumerate(data["ids"]):
        meta = data["metadatas"][i]
        faqs.append({
            "id": doc_id,
            "tag": meta.get("tag", "Umum"),
            "judul": meta.get("judul", ""),
            "jawaban_tampil": meta.get("jawaban_tampil", ""),
            "keywords_raw": meta.get("keywords_raw", ""),
            "path_gambar": meta.get("path_gambar", "none"),
            "sumber_url": meta.get("sumber_url", ""),
        })

    os.makedirs(os.path.dirname(EXPORT_FILE), exist_ok=True)
    with open(EXPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(faqs, f, indent=2, ensure_ascii=False)

    print(f"Exported {len(faqs)} FAQs to {EXPORT_FILE}")


def import_to_typesense():
    """Import FAQs from JSON file into Typesense via FAQService."""
    # Add project root to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    if not os.path.exists(EXPORT_FILE):
        print(f"Export file not found: {EXPORT_FILE}")
        print("Run 'python scripts/migrate_chroma_to_typesense.py export' first.")
        return

    with open(EXPORT_FILE, "r", encoding="utf-8") as f:
        faqs = json.load(f)

    print(f"Loaded {len(faqs)} FAQs from {EXPORT_FILE}")

    # Import services (this initializes Typesense connection)
    from config import container
    from app.services.faq_service import FAQService

    # Ensure vector store is ready
    container.get_vector_store()
    container.get_embedding()

    success = 0
    failed = 0

    for i, faq in enumerate(faqs):
        try:
            FAQService.upsert(
                tag=faq["tag"],
                judul=faq["judul"],
                jawaban=faq["jawaban_tampil"],
                keywords=faq["keywords_raw"],
                img_paths=faq["path_gambar"],
                source_url=faq["sumber_url"],
                doc_id=faq["id"],
            )
            success += 1
            print(f"  [{i+1}/{len(faqs)}] Imported: {faq['judul'][:60]}")
        except Exception as e:
            failed += 1
            print(f"  [{i+1}/{len(faqs)}] FAILED: {faq['judul'][:60]} — {e}")

    print(f"\nDone! Success: {success}, Failed: {failed}")
    if failed == 0:
        print("Migration complete. You can now remove the old ChromaDB container.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/migrate_chroma_to_typesense.py export")
        print("  python scripts/migrate_chroma_to_typesense.py import")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "export":
        export_from_chroma()
    elif command == "import":
        import_to_typesense()
    else:
        print(f"Unknown command: {command}")
        print("Use 'export' or 'import'")
        sys.exit(1)
