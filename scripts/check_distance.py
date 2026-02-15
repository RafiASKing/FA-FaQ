"""Quick check: what distance values does Typesense actually return?"""
from config import container
from app.services.embedding_service import EmbeddingService

queries = ["nasi padang", "tombol call pasien abu-abu", "sate kambing", "cara input obat"]

for q in queries:
    query_vec = EmbeddingService.generate_query_embedding(q)
    store = container.get_vector_store()
    results = store.query(query_embedding=query_vec, n_results=1)

    if results:
        r = results[0]
        judul = r.metadata.get("judul", "?")
        
        # Typesense returns COSINE DISTANCE (0-2 range)
        cosine_dist = r.distance
        cosine_sim = 1 - cosine_dist
        
        # Current formula (designed for ChromaDB L2)
        current_score = max(0, (1 - cosine_dist) * 100)
        
        # What ChromaDB would have returned (L2² = 2 * cosine_distance for normalized vectors)
        equiv_l2_squared = 2 * cosine_dist
        chromadb_score = max(0, (1 - equiv_l2_squared) * 100)
        
        print(f"Query: {q}")
        print(f"  Top match: {judul[:40]}")
        print(f"  Raw distance (Typesense cosine): {cosine_dist:.4f}")
        print(f"  Cosine similarity: {cosine_sim:.4f}")
        print(f"  Current score (Typesense):  {current_score:.1f}%")
        print(f"  Equiv score (ChromaDB L2²): {chromadb_score:.1f}%")
        print()
