"""
Re-embed Script - Regenerate embeddings for all documents.

Use this after changing the embedding template or model.
Reads all docs from Typesense, generates new embeddings, updates in place.

Usage:
    python scripts/reembed_all.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from config.settings import settings
from config.constants import EMBEDDING_DIMENSION
from config.typesenseDb import TypesenseVectorStoreAdapter
from app.services.embedding_service import EmbeddingService


def main():
    print("=" * 60)
    print("🔄 Re-embed All Documents")
    print("=" * 60)
    
    # Connect to Typesense
    store = TypesenseVectorStoreAdapter(
        host=settings.typesense_host,
        port=settings.typesense_port,
        api_key=settings.typesense_api_key,
        collection_name=settings.typesense_collection,
        embedding_dim=EMBEDDING_DIMENSION,
    )
    
    # Get all documents
    docs = store.get_all(include_documents=True)
    print(f"📂 Found {len(docs)} documents\n")
    
    if not docs:
        print("⚠️  No documents to re-embed.")
        return
    
    # Confirm
    confirm = input("❓ Re-embed all documents? (y/N): ").strip().lower()
    if confirm != "y":
        print("❌ Cancelled.")
        return
    
    print()
    
    success = 0
    errors = 0
    
    for i, doc in enumerate(docs, 1):
        try:
            meta = doc.metadata
            print(f"  [{i}/{len(docs)}] {meta.get('judul', 'N/A')[:50]}...")
            
            tag = meta.get("tag", "")
            judul = meta.get("judul", "")
            jawaban = meta.get("jawaban_tampil", "")
            keywords = meta.get("keywords_raw", "")
            
            # Generate embedding AND document text (single source of truth)
            embedding, new_document = EmbeddingService.build_faq_document(
                tag=tag,
                judul=judul,
                jawaban=jawaban,
                keywords=keywords,
            )
            
            # Update in Typesense
            store.upsert(
                doc_id=doc.id,
                embedding=embedding,
                document=new_document,
                metadata=meta,
            )
            
            success += 1
            print(f"       ✅ Done")
            
        except Exception as e:
            errors += 1
            print(f"       ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("📊 Complete!")
    print("=" * 60)
    print(f"   ✅ Success: {success}")
    print(f"   ❌ Errors:  {errors}")


if __name__ == "__main__":
    main()
