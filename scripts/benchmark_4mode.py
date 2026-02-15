"""
Full 4-Mode Embedding Benchmark
================================
Creates a TEMPORARY Typesense collection with old-template embeddings,
then tests all 4 combinations:

  1. Old Template + Symmetric  (RETRIEVAL_DOCUMENT → RETRIEVAL_DOCUMENT) ← prod-like
  2. Old Template + Asymmetric (RETRIEVAL_DOCUMENT → RETRIEVAL_QUERY)
  3. New Template + Symmetric  (RETRIEVAL_DOCUMENT → RETRIEVAL_DOCUMENT)
  4. New Template + Asymmetric (RETRIEVAL_DOCUMENT → RETRIEVAL_QUERY)   ← current

Usage:
    $env:PYTHONPATH="."; python scripts/benchmark_4mode.py
"""

import time
import typesense
from typing import List, Tuple
from dataclasses import dataclass

from config import container
from config.settings import settings
from config.constants import EMBEDDING_DIMENSION
from app.services.search_service import SearchService
from core.tag_manager import TagManager
from core.content_parser import ContentParser


# ============================================================
# CONFIG
# ============================================================
TEMP_COLLECTION = "benchmark_old_template"

# ============================================================
# TEST QUERIES — mix of long and short
# ============================================================

# RELEVANT - should match (query, expected_title_substring)
RELEVANT_QUERIES = [
    # Long queries
    ("tombol call pasien saya abu-abu gabisa diklik", "Call"),
    ("gabisa login di hp nurse ipd", "Nurse Tidak Bisa"),
    ("cara nambah resep obat di soap", "Resep Obat"),
    ("form apa aja yang belum ada di emr ed?", "form di EMR ED"),
    ("data yang wajib diisi di soap itu apa aja?", "mandatory"),
    ("bisa gak order obat sebelum asesmen perawat?", "order obat sebelum"),
    ("kenapa discharge pasien error gabisa?", "Discharge"),
    ("template soap rehab kok gak ada therapy plan?", "Therapy Plan"),
    # Short queries
    ("obat", "Resep Obat"),
    ("form ed", "form di EMR ED"),
    ("discharge", "Discharge"),
    ("call pasien", "Call"),
    ("resep", "Resep Obat"),
    ("referral", "Referral"),
    ("mcu", "mcu"),
    ("soap", "SOAP"),
    ("initial assessment", "Initial"),
    ("nurse ipd", "Nurse"),
    ("print lab", "print"),
    ("drip obat", "drip"),
]

# IRRELEVANT - obviously off-topic
IRRELEVANT_QUERIES = [
    "makan nasi padang yok",
    "sate kambing enak banget",
    "siapa presiden indonesia sekarang?",
    "harga tiket pesawat jakarta bali",
    "resep kue brownies coklat",
    # Short
    "nasi padang",
    "bola",
    "cuaca",
    "iphone",
    "musik",
]

# TRICKY - hospital-sounding but no FAQ exists
TRICKY_QUERIES = [
    "cara reset password emr saya lupa",
    "bagaimana cara transfer pasien antar ruangan?",
    "dimana menu untuk input hasil radiologi?",
    "cara bikin surat rujukan BPJS",
    "gimana caranya booking ruang operasi?",
    # Short
    "jadwal dokter",
    "reset password",
    "radiologi",
    "bpjs",
    "transfer pasien",
]

# ============================================================
# TEMPLATE BUILDERS
# ============================================================

def build_old_template(tag: str, judul: str, jawaban: str, keywords: str) -> str:
    """Old template: DOMAIN / DOKUMEN / VARIASI PERTANYAAN USER / ISI KONTEN"""
    clean_jawaban = ContentParser.clean_for_embedding(jawaban)
    try:
        tag_desc = TagManager.get_tag_description(tag)
    except:
        tag_desc = ""
    domain_str = f"{tag} ({tag_desc})" if tag_desc else tag

    return f"""DOMAIN: {domain_str}
DOKUMEN: {judul}
VARIASI PERTANYAAN USER: {keywords}
ISI KONTEN: {clean_jawaban}"""


def build_new_template(tag: str, judul: str, jawaban: str, keywords: str) -> str:
    """New template: MODUL / TOPIK / TERKAIT / ISI KONTEN"""
    clean_jawaban = ContentParser.clean_for_embedding(jawaban)
    try:
        tag_desc = TagManager.get_tag_description(tag)
    except:
        tag_desc = ""
    domain_str = f"{tag} ({tag_desc})" if tag_desc else tag

    return f"""MODUL: {domain_str}
TOPIK: {judul}
TERKAIT: {keywords}
ISI KONTEN: {clean_jawaban}"""


# ============================================================
# TYPESENSE TEMP COLLECTION
# ============================================================

def get_typesense_client():
    return typesense.Client({
        "nodes": [{
            "host": settings.typesense_host,
            "port": str(settings.typesense_port),
            "protocol": "http"
        }],
        "api_key": settings.typesense_api_key,
        "connection_timeout_seconds": 10
    })


def create_temp_collection(client):
    """Create temporary collection for old template embeddings."""
    # Delete if exists
    try:
        client.collections[TEMP_COLLECTION].delete()
        print(f"  Deleted existing {TEMP_COLLECTION}")
    except:
        pass

    schema = {
        "name": TEMP_COLLECTION,
        "fields": [
            {"name": "id", "type": "string"},
            {"name": "tag", "type": "string", "facet": True},
            {"name": "judul", "type": "string"},
            {"name": "jawaban_tampil", "type": "string"},
            {"name": "keywords_raw", "type": "string"},
            {"name": "path_gambar", "type": "string"},
            {"name": "sumber_url", "type": "string"},
            {"name": "document", "type": "string"},
            {"name": "embedding", "type": "float[]", "num_dim": EMBEDDING_DIMENSION},
        ]
    }
    client.collections.create(schema)
    print(f"  Created {TEMP_COLLECTION}")


def populate_old_template_collection(client):
    """Re-embed all docs with old template and insert into temp collection."""
    # Get all docs from current (new template) collection
    store = container.get_vector_store()
    all_docs = store.get_all(include_documents=False)
    
    embed_fn = container.get_embedding()
    
    print(f"  Re-embedding {len(all_docs)} documents with OLD template...")
    
    for i, doc in enumerate(all_docs):
        tag = doc.metadata.get("tag", "")
        judul = doc.metadata.get("judul", "")
        jawaban = doc.metadata.get("jawaban_tampil", "")
        keywords = doc.metadata.get("keywords_raw", "")
        
        # Build old template text
        old_text = build_old_template(tag, judul, jawaban, keywords)
        
        # Embed with RETRIEVAL_DOCUMENT (how docs are always embedded)
        embedding = embed_fn.embed(old_text, task_type="RETRIEVAL_DOCUMENT")
        
        if not embedding:
            print(f"    ⚠️ Failed to embed doc {doc.id}: {judul}")
            continue
        
        # Insert into temp collection
        typesense_doc = {
            "id": doc.id,
            "tag": tag,
            "judul": judul,
            "jawaban_tampil": jawaban,
            "keywords_raw": keywords,
            "path_gambar": doc.metadata.get("path_gambar", ""),
            "sumber_url": doc.metadata.get("sumber_url", ""),
            "document": old_text,
            "embedding": embedding,
        }
        
        client.collections[TEMP_COLLECTION].documents.upsert(typesense_doc)
        print(f"    [{i+1}/{len(all_docs)}] {tag}: {judul[:40]}")
    
    print(f"  ✅ Done! {len(all_docs)} documents embedded with old template.")


def cleanup_temp_collection(client):
    """Delete temporary collection."""
    try:
        client.collections[TEMP_COLLECTION].delete()
        print(f"\n🧹 Cleaned up temp collection: {TEMP_COLLECTION}")
    except:
        pass


# ============================================================
# SEARCH FUNCTIONS
# ============================================================

def search_collection(client, collection_name: str, query: str,
                      task_type: str) -> Tuple[float, str]:
    """Search a specific collection with specified task type."""
    embed_fn = container.get_embedding()
    embedding = embed_fn.embed(query, task_type=task_type)
    
    if not embedding:
        return 0.0, "ERROR"
    
    search_request = {
        "searches": [{
            "collection": collection_name,
            "q": "*",
            "vector_query": f"embedding:([], k:1)",
            "exclude_fields": "embedding",
        }]
    }
    
    try:
        response = client.multi_search.perform(
            search_request,
            {"vector_query": f"embedding:([{','.join(map(str, embedding))}], k:1)"}
        )
        
        search_result = response.get("results", [{}])[0]
        hits = search_result.get("hits", [])
        
        if not hits:
            return 0.0, "NO RESULTS"
        
        hit = hits[0]
        distance = hit.get("vector_distance", 1.0)
        score = SearchService.calculate_relevance(distance)
        title = hit.get("document", {}).get("judul", "?")
        
        return score, title
    
    except Exception as e:
        print(f"    Search error: {e}")
        return 0.0, "ERROR"


# ============================================================
# BENCHMARK
# ============================================================

@dataclass
class Result:
    query: str
    category: str
    top_score: float
    top_title: str
    mode: str


def run_benchmark():
    client = get_typesense_client()
    results: List[Result] = []
    
    # --- STEP 1: Create temp collection with old template ---
    print(f"\n{'='*80}")
    print("STEP 1: Creating old-template collection")
    print(f"{'='*80}\n")
    
    create_temp_collection(client)
    populate_old_template_collection(client)
    
    # --- STEP 2: Define 4 modes ---
    current_collection = settings.typesense_collection  # new template docs
    
    modes = [
        ("Old+Sym",   TEMP_COLLECTION,    "RETRIEVAL_DOCUMENT", "Old Template + Symmetric (like prod)"),
        ("Old+Asym",  TEMP_COLLECTION,    "RETRIEVAL_QUERY",    "Old Template + Asymmetric"),
        ("New+Sym",   current_collection, "RETRIEVAL_DOCUMENT", "New Template + Symmetric"),
        ("New+Asym",  current_collection, "RETRIEVAL_QUERY",    "New Template + Asymmetric (current)"),
    ]
    
    total_queries = len(RELEVANT_QUERIES) + len(IRRELEVANT_QUERIES) + len(TRICKY_QUERIES)
    total_runs = total_queries * len(modes)
    count = 0
    
    # --- STEP 3: Run benchmark ---
    print(f"\n{'='*80}")
    print(f"STEP 2: Running benchmark ({total_runs} searches)")
    print(f"{'='*80}")
    
    for mode_key, collection, task_type, mode_desc in modes:
        print(f"\n--- {mode_desc} ---")
        print(f"    Collection: {collection} | Query task_type: {task_type}\n")
        
        for query, expected in RELEVANT_QUERIES:
            count += 1
            score, title = search_collection(client, collection, query, task_type)
            short_q = query[:35].ljust(35)
            print(f"  [{count:>3}/{total_runs}] ✅ {short_q} → {score:.1f}% {title[:30]}")
            results.append(Result(query, "RELEVANT", score, title, mode_key))
        
        for query in IRRELEVANT_QUERIES:
            count += 1
            score, title = search_collection(client, collection, query, task_type)
            short_q = query[:35].ljust(35)
            print(f"  [{count:>3}/{total_runs}] ❌ {short_q} → {score:.1f}% {title[:30]}")
            results.append(Result(query, "IRRELEVANT", score, title, mode_key))
        
        for query in TRICKY_QUERIES:
            count += 1
            score, title = search_collection(client, collection, query, task_type)
            short_q = query[:35].ljust(35)
            print(f"  [{count:>3}/{total_runs}] ⚠️  {short_q} → {score:.1f}% {title[:30]}")
            results.append(Result(query, "TRICKY", score, title, mode_key))
    
    # --- STEP 4: Analysis ---
    print(f"\n\n{'='*80}")
    print("STEP 3: ANALYSIS")
    print(f"{'='*80}")
    
    summary_rows = []
    
    for mode_key, _, _, mode_desc in modes:
        mr = [r for r in results if r.mode == mode_key]
        
        rel = [r.top_score for r in mr if r.category == "RELEVANT"]
        irr = [r.top_score for r in mr if r.category == "IRRELEVANT"]
        tri = [r.top_score for r in mr if r.category == "TRICKY"]
        
        rel_min, rel_avg, rel_max = min(rel), sum(rel)/len(rel), max(rel)
        irr_min, irr_avg, irr_max = min(irr), sum(irr)/len(irr), max(irr)
        tri_min, tri_avg, tri_max = min(tri), sum(tri)/len(tri), max(tri)
        
        noise_max = max(irr_max, tri_max)
        gap = rel_min - noise_max
        
        summary_rows.append({
            "mode": mode_key,
            "desc": mode_desc,
            "rel_min": rel_min, "rel_avg": rel_avg, "rel_max": rel_max,
            "irr_max": irr_max, "tri_max": tri_max,
            "noise_max": noise_max, "gap": gap,
        })
        
        print(f"\n--- {mode_desc} ---")
        print(f"  RELEVANT   : min={rel_min:.1f}%  avg={rel_avg:.1f}%  max={rel_max:.1f}%")
        print(f"  IRRELEVANT : min={irr_min:.1f}%  avg={irr_avg:.1f}%  max={irr_max:.1f}%")
        print(f"  TRICKY     : min={tri_min:.1f}%  avg={tri_avg:.1f}%  max={tri_max:.1f}%")
        print(f"  GAP (rel_min - noise_max): {gap:.1f}%")
        
        if gap > 0:
            threshold = (rel_min + noise_max) / 2
            print(f"  ✅ CLEAN SEPARATION! Suggested threshold: {threshold:.0f}%")
        else:
            print(f"  ⚠️  OVERLAP of {abs(gap):.1f}% — no clean threshold possible")
    
    # --- COMPARISON TABLE ---
    print(f"\n\n{'='*80}")
    print("COMPARISON TABLE")
    print(f"{'='*80}\n")
    
    header = f"{'Mode':<35} {'Rel min':>8} {'Rel avg':>8} {'Irr max':>8} {'Tri max':>8} {'GAP':>8} {'Verdict':>12}"
    print(header)
    print("─" * len(header))
    
    for row in summary_rows:
        verdict = "✅ CLEAN" if row["gap"] > 0 else f"⚠️ -{abs(row['gap']):.1f}%"
        print(f"{row['desc']:<35} {row['rel_min']:>7.1f}% {row['rel_avg']:>7.1f}% "
              f"{row['irr_max']:>7.1f}% {row['tri_max']:>7.1f}% {row['gap']:>7.1f}% {verdict:>12}")
    
    # --- SIDE-BY-SIDE per query ---
    print(f"\n\n{'='*80}")
    print("SIDE-BY-SIDE: ALL QUERIES")
    print(f"{'='*80}\n")
    
    mode_keys = [m[0] for m in modes]
    
    header = f"{'Cat':>3} {'Query':<38}"
    for mk in mode_keys:
        header += f" {mk:>10}"
    print(header)
    print("─" * len(header))
    
    all_queries = (
        [(q, "R", e) for q, e in RELEVANT_QUERIES] +
        [(q, "I", "") for q in IRRELEVANT_QUERIES] +
        [(q, "T", "") for q in TRICKY_QUERIES]
    )
    
    for query, cat, _ in all_queries:
        marker = {"R": "✅", "I": "❌", "T": "⚠️"}[cat]
        line = f" {marker} {query[:36]:<38}"
        for mk in mode_keys:
            score = next((r.top_score for r in results
                         if r.mode == mk and r.query == query), 0)
            line += f" {score:>9.1f}%"
        print(line)
    
    # --- CLEANUP ---
    cleanup_temp_collection(client)


if __name__ == "__main__":
    start = time.time()
    run_benchmark()
    elapsed = time.time() - start
    print(f"\nBenchmark completed in {elapsed:.1f}s")
