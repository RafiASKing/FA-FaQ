"""
Head-to-Head: Old System vs New System
=======================================
Simulates EXACTLY how each system would behave:

OLD SYSTEM (Production):
  - Old template (DOMAIN/DOKUMEN/VARIASI PERTANYAAN USER/ISI KONTEN)
  - Symmetric: RETRIEVAL_DOCUMENT for both docs and queries
  - ChromaDB L2² distance formula: (1 - 2*cosine_dist) * 100
  - Threshold: 41%

NEW SYSTEM (Current + fix):
  - New template (MODUL/TOPIK/TERKAIT/ISI KONTEN)
  - Asymmetric: RETRIEVAL_QUERY for queries, RETRIEVAL_DOCUMENT for docs
  - Typesense cosine formula: (1 - cosine_dist) * 100
  - Threshold: 70% (calibrated equivalent of old 41%)

Usage:
    $env:PYTHONPATH="."; python scripts/benchmark_headtohead.py
"""

import time
import typesense
from typing import List, Tuple
from dataclasses import dataclass

from config import container
from config.settings import settings
from config.constants import EMBEDDING_DIMENSION
from core.tag_manager import TagManager
from core.content_parser import ContentParser


TEMP_COLLECTION = "benchmark_old_template"

# Thresholds
OLD_THRESHOLD = 41.0    # ChromaDB L2² scale
NEW_THRESHOLD = 70.0    # Typesense cosine scale (equivalent to old 41%)

# ============================================================
# TEST QUERIES — comprehensive mix
# ============================================================

RELEVANT_QUERIES = [
    # Long
    ("tombol call pasien saya abu-abu gabisa diklik", "Call"),
    ("gabisa login di hp nurse ipd", "Nurse"),
    ("cara nambah resep obat di soap", "Resep Obat"),
    ("form apa aja yang belum ada di emr ed?", "form di EMR ED"),
    ("kenapa discharge pasien error gabisa?", "Discharge"),
    ("data yang wajib diisi di soap itu apa aja?", "mandatory"),
    ("template soap rehab kok gak ada therapy plan?", "Therapy Plan"),
    ("bisa gak order obat sebelum asesmen perawat?", "order obat"),
    ("cashier mau print form lab dari igd bisa gak?", "cashier"),
    ("obat drip bisa diresepkan gak?", "drip"),
    # Short
    ("obat", "Resep"),
    ("form ed", "form"),
    ("discharge", "Discharge"),
    ("call pasien", "Call"),
    ("resep", "Resep"),
    ("referral", "Referral"),
    ("mcu", "mcu"),
    ("soap", "SOAP"),
    ("nurse ipd", "Nurse"),
    ("print lab", "print"),
]

IRRELEVANT_QUERIES = [
    "makan nasi padang yok",
    "sate kambing enak banget",
    "siapa presiden indonesia sekarang?",
    "harga tiket pesawat jakarta bali",
    "resep kue brownies coklat",
    "berapa harga iphone 16 pro max?",
    "manchester united menang berapa?",
    "nasi padang",
    "bola",
    "musik",
]

TRICKY_QUERIES = [
    "cara reset password emr saya lupa",
    "bagaimana cara transfer pasien antar ruangan?",
    "dimana menu untuk input hasil radiologi?",
    "cara bikin surat rujukan BPJS",
    "gimana caranya booking ruang operasi?",
    "jadwal dokter",
    "reset password",
    "radiologi",
    "bpjs",
    "transfer pasien",
]


# ============================================================
# TEMPLATES
# ============================================================

def build_old_template(tag, judul, jawaban, keywords):
    clean = ContentParser.clean_for_embedding(jawaban)
    try: desc = TagManager.get_tag_description(tag)
    except: desc = ""
    domain = f"{tag} ({desc})" if desc else tag
    return f"DOMAIN: {domain}\nDOKUMEN: {judul}\nVARIASI PERTANYAAN USER: {keywords}\nISI KONTEN: {clean}"

def build_new_template(tag, judul, jawaban, keywords):
    clean = ContentParser.clean_for_embedding(jawaban)
    try: desc = TagManager.get_tag_description(tag)
    except: desc = ""
    domain = f"{tag} ({desc})" if desc else tag
    return f"MODUL: {domain}\nTOPIK: {judul}\nTERKAIT: {keywords}\nISI KONTEN: {clean}"


# ============================================================
# SCORE FORMULAS
# ============================================================

def score_old_chromadb(cosine_distance: float) -> float:
    """ChromaDB L2² equivalent: (1 - 2*cosine_dist) * 100"""
    return max(0, (1 - 2 * cosine_distance) * 100)

def score_new_typesense(cosine_distance: float) -> float:
    """Typesense cosine similarity: (1 - cosine_dist) * 100"""
    return max(0, (1 - cosine_distance) * 100)


# ============================================================
# TYPESENSE HELPERS
# ============================================================

def get_client():
    return typesense.Client({
        "nodes": [{"host": settings.typesense_host, "port": str(settings.typesense_port), "protocol": "http"}],
        "api_key": settings.typesense_api_key,
        "connection_timeout_seconds": 10
    })

def setup_old_collection(client):
    try: client.collections[TEMP_COLLECTION].delete()
    except: pass
    
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
    
    store = container.get_vector_store()
    all_docs = store.get_all(include_documents=False)
    embed_fn = container.get_embedding()
    
    print(f"  Re-embedding {len(all_docs)} docs with OLD template...")
    for i, doc in enumerate(all_docs):
        m = doc.metadata
        old_text = build_old_template(m.get("tag",""), m.get("judul",""), m.get("jawaban_tampil",""), m.get("keywords_raw",""))
        emb = embed_fn.embed(old_text, task_type="RETRIEVAL_DOCUMENT")
        if not emb: continue
        client.collections[TEMP_COLLECTION].documents.upsert({
            "id": doc.id, "tag": m.get("tag",""), "judul": m.get("judul",""),
            "jawaban_tampil": m.get("jawaban_tampil",""), "keywords_raw": m.get("keywords_raw",""),
            "path_gambar": m.get("path_gambar",""), "sumber_url": m.get("sumber_url",""),
            "document": old_text, "embedding": emb,
        })
        print(f"    [{i+1}/{len(all_docs)}] {m.get('judul','')[:40]}")
    print(f"  ✅ Done!")


def search_raw(client, collection, query, task_type):
    """Returns raw cosine distance from Typesense."""
    emb = container.get_embedding().embed(query, task_type=task_type)
    if not emb: return 1.0, "ERROR"
    
    req = {"searches": [{"collection": collection, "q": "*",
           "vector_query": f"embedding:([], k:1)", "exclude_fields": "embedding"}]}
    resp = client.multi_search.perform(req,
           {"vector_query": f"embedding:([{','.join(map(str, emb))}], k:1)"})
    
    hits = resp.get("results", [{}])[0].get("hits", [])
    if not hits: return 1.0, "NO RESULTS"
    
    dist = hits[0].get("vector_distance", 1.0)
    title = hits[0].get("document", {}).get("judul", "?")
    return dist, title


# ============================================================
# MAIN BENCHMARK
# ============================================================

def run():
    client = get_client()
    
    print(f"\n{'='*90}")
    print("HEAD-TO-HEAD: OLD SYSTEM vs NEW SYSTEM")
    print(f"{'='*90}")
    
    # Setup old collection
    print(f"\nSetting up old-template collection...")
    setup_old_collection(client)
    
    current_col = settings.typesense_collection
    total = len(RELEVANT_QUERIES) + len(IRRELEVANT_QUERIES) + len(TRICKY_QUERIES)
    
    print(f"\nRunning {total} queries x 2 systems = {total*2} searches...\n")
    
    # Collect results
    rows = []
    count = 0
    
    all_queries = (
        [("R", q, e) for q, e in RELEVANT_QUERIES] +
        [("I", q, "") for q in IRRELEVANT_QUERIES] +
        [("T", q, "") for q in TRICKY_QUERIES]
    )
    
    for cat, query, expected in all_queries:
        count += 1
        
        # OLD SYSTEM: old template + symmetric + L2² formula
        old_dist, old_title = search_raw(client, TEMP_COLLECTION, query, "RETRIEVAL_DOCUMENT")
        old_score = score_old_chromadb(old_dist)
        old_pass = old_score > OLD_THRESHOLD
        
        # NEW SYSTEM: new template + asymmetric + cosine formula
        new_dist, new_title = search_raw(client, current_col, query, "RETRIEVAL_QUERY")
        new_score = score_new_typesense(new_dist)
        new_pass = new_score > NEW_THRESHOLD
        
        marker = {"R": "✅", "I": "❌", "T": "⚠️"}[cat]
        print(f"  [{count:>2}/{total}] {marker} {query[:38]:<40}  "
              f"OLD: {old_score:5.1f}% {'PASS' if old_pass else 'FAIL':>4}  |  "
              f"NEW: {new_score:5.1f}% {'PASS' if new_pass else 'FAIL':>4}")
        
        rows.append({
            "cat": cat, "query": query, "expected": expected,
            "old_score": old_score, "old_pass": old_pass, "old_title": old_title,
            "new_score": new_score, "new_pass": new_pass, "new_title": new_title,
        })
    
    # ============================================================
    # ANALYSIS
    # ============================================================
    print(f"\n\n{'='*90}")
    print("FILTERING ACCURACY")
    print(f"{'='*90}\n")
    
    for sys_name, score_key, pass_key, threshold in [
        ("OLD SYSTEM (L2², threshold 41%)", "old_score", "old_pass", OLD_THRESHOLD),
        ("NEW SYSTEM (cosine, threshold 70%)", "new_score", "new_pass", NEW_THRESHOLD),
    ]:
        relevant_rows = [r for r in rows if r["cat"] == "R"]
        irrelevant_rows = [r for r in rows if r["cat"] == "I"]
        tricky_rows = [r for r in rows if r["cat"] == "T"]
        
        # True positives: relevant queries that PASS
        tp = sum(1 for r in relevant_rows if r[pass_key])
        fn = len(relevant_rows) - tp
        
        # True negatives: irrelevant/tricky that FAIL (correctly rejected)
        tn_irr = sum(1 for r in irrelevant_rows if not r[pass_key])
        fp_irr = len(irrelevant_rows) - tn_irr
        
        tn_tri = sum(1 for r in tricky_rows if not r[pass_key])
        fp_tri = len(tricky_rows) - tn_tri
        
        recall = tp / len(relevant_rows) * 100 if relevant_rows else 0
        irr_reject = tn_irr / len(irrelevant_rows) * 100 if irrelevant_rows else 0
        tri_reject = tn_tri / len(tricky_rows) * 100 if tricky_rows else 0
        
        total_correct = tp + tn_irr + tn_tri
        total_possible = len(rows)
        accuracy = total_correct / total_possible * 100
        
        print(f"--- {sys_name} ---")
        print(f"  Relevant passed (recall):     {tp}/{len(relevant_rows)} = {recall:.0f}%")
        print(f"  Irrelevant rejected:          {tn_irr}/{len(irrelevant_rows)} = {irr_reject:.0f}%")
        print(f"  Tricky rejected:              {tn_tri}/{len(tricky_rows)} = {tri_reject:.0f}%")
        print(f"  Overall accuracy:             {total_correct}/{total_possible} = {accuracy:.0f}%")
        
        # Show failures
        if fn > 0:
            print(f"\n  ⚠️ Relevant queries MISSED (false negatives):")
            for r in relevant_rows:
                if not r[pass_key]:
                    print(f"      {r['query'][:45]} → {r[score_key]:.1f}% (below {threshold}%)")
        
        if fp_irr > 0:
            print(f"\n  ⚠️ Irrelevant queries LEAKED (false positives):")
            for r in irrelevant_rows:
                if r[pass_key]:
                    print(f"      {r['query'][:45]} → {r[score_key]:.1f}% (above {threshold}%)")
        
        if fp_tri > 0:
            print(f"\n  ⚠️ Tricky queries LEAKED (false positives):")
            for r in tricky_rows:
                if r[pass_key]:
                    print(f"      {r['query'][:45]} → {r[score_key]:.1f}% (above {threshold}%)")
        
        print()
    
    # ============================================================
    # SCORE DISTRIBUTION
    # ============================================================
    print(f"\n{'='*90}")
    print("SCORE RANGES")
    print(f"{'='*90}\n")
    
    for sys_name, score_key, threshold in [
        ("OLD (L2², 41%)", "old_score", OLD_THRESHOLD),
        ("NEW (cosine, 70%)", "new_score", NEW_THRESHOLD),
    ]:
        rel = [r[score_key] for r in rows if r["cat"] == "R"]
        irr = [r[score_key] for r in rows if r["cat"] == "I"]
        tri = [r[score_key] for r in rows if r["cat"] == "T"]
        
        gap = min(rel) - max(max(irr), max(tri))
        
        print(f"--- {sys_name} ---")
        print(f"  Relevant:    {min(rel):.1f}% — {max(rel):.1f}%  (avg {sum(rel)/len(rel):.1f}%)")
        print(f"  Irrelevant:  {min(irr):.1f}% — {max(irr):.1f}%  (avg {sum(irr)/len(irr):.1f}%)")
        print(f"  Tricky:      {min(tri):.1f}% — {max(tri):.1f}%  (avg {sum(tri)/len(tri):.1f}%)")
        print(f"  Threshold:   {threshold}%  |  GAP: {gap:.1f}%")
        print()
    
    # Cleanup
    try: client.collections[TEMP_COLLECTION].delete()
    except: pass
    print(f"🧹 Cleaned up temp collection")


if __name__ == "__main__":
    start = time.time()
    run()
    print(f"\nCompleted in {time.time()-start:.1f}s")
