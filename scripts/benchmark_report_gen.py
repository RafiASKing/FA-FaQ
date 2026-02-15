"""
Rerun head-to-head with FULL detail output (including retrieved titles).
Saves results to a markdown file directly.

Usage:
    $env:PYTHONPATH="."; python scripts/benchmark_report_gen.py
"""

import time
import typesense
from typing import List, Tuple

from config import container
from config.settings import settings
from config.constants import EMBEDDING_DIMENSION
from app.services.search_service import SearchService
from core.tag_manager import TagManager
from core.content_parser import ContentParser


TEMP_COLLECTION = "benchmark_old_template"
OLD_THRESHOLD = 41.0
NEW_THRESHOLD = 70.0
REPORT_FILE = "docs/BENCHMARK_HEADTOHEAD_REPORT.md"

# Queries
RELEVANT_QUERIES = [
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


def build_old_template(tag, judul, jawaban, keywords):
    clean = ContentParser.clean_for_embedding(jawaban)
    try: desc = TagManager.get_tag_description(tag)
    except: desc = ""
    domain = f"{tag} ({desc})" if desc else tag
    return f"DOMAIN: {domain}\nDOKUMEN: {judul}\nVARIASI PERTANYAAN USER: {keywords}\nISI KONTEN: {clean}"


def score_old(cosine_dist):
    return max(0, (1 - 2 * cosine_dist) * 100)

def score_new(cosine_dist):
    return max(0, (1 - cosine_dist) * 100)


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
    
    print(f"Re-embedding {len(all_docs)} docs with OLD template...")
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
        print(f"  [{i+1}/{len(all_docs)}] {m.get('judul','')[:50]}")
    print(f"✅ Done!")


def search_raw(client, collection, query, task_type):
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


def run():
    client = get_client()
    current_col = settings.typesense_collection
    
    print("Setting up old-template collection...")
    setup_old_collection(client)
    
    # Collect results
    rows = []
    all_queries = (
        [("R", q, e) for q, e in RELEVANT_QUERIES] +
        [("I", q, "") for q in IRRELEVANT_QUERIES] +
        [("T", q, "") for q in TRICKY_QUERIES]
    )
    
    total = len(all_queries)
    print(f"\nRunning {total} queries x 2 systems...\n")
    
    for i, (cat, query, expected) in enumerate(all_queries):
        # OLD: old template collection + symmetric
        old_dist, old_title = search_raw(client, TEMP_COLLECTION, query, "RETRIEVAL_DOCUMENT")
        old_score = score_old(old_dist)
        old_pass = old_score > OLD_THRESHOLD
        
        # NEW: new template collection + asymmetric
        new_dist, new_title = search_raw(client, current_col, query, "RETRIEVAL_QUERY")
        new_score = score_new(new_dist)
        new_pass = new_score > NEW_THRESHOLD
        
        marker = {"R": "✅", "I": "❌", "T": "⚠️"}[cat]
        same = "SAME" if old_title == new_title else "DIFF ⚡"
        
        print(f"[{i+1:>2}/{total}] {marker} {query[:35]:<37} "
              f"OLD:{old_score:5.1f}%→{old_title[:25]:<25} | "
              f"NEW:{new_score:5.1f}%→{new_title[:25]:<25} [{same}]")
        
        rows.append({
            "cat": cat, "query": query,
            "old_score": old_score, "old_pass": old_pass, "old_title": old_title,
            "new_score": new_score, "new_pass": new_pass, "new_title": new_title,
        })
    
    # Generate report
    print(f"\n\nGenerating report to {REPORT_FILE}...")
    
    lines = []
    lines.append("# Head-to-Head Benchmark Report")
    lines.append(f"> **Date**: 2026-02-15 (re-run) | **Queries**: {total} × 2 systems = {total*2} searches")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## System Configurations")
    lines.append("")
    lines.append("| | OLD System | NEW System |")
    lines.append("|---|---|---|")
    lines.append("| **Template** | `DOMAIN / DOKUMEN / VARIASI PERTANYAAN USER / ISI KONTEN` | `MODUL / TOPIK / TERKAIT / ISI KONTEN` |")
    lines.append("| **Doc Embedding** | `RETRIEVAL_DOCUMENT` | `RETRIEVAL_DOCUMENT` |")
    lines.append("| **Query Embedding** | `RETRIEVAL_DOCUMENT` (symmetric) | `RETRIEVAL_QUERY` (asymmetric) |")
    lines.append("| **Score Formula** | `(1 - 2×cosine_dist) × 100` (ChromaDB L2²) | `(1 - cosine_dist) × 100` (Typesense cosine) |")
    lines.append("| **Threshold** | 41% | 70% |")
    lines.append("| **Embedding Model** | `gemini-embedding-001` (3072-dim) | `gemini-embedding-001` (3072-dim) |")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Overall accuracy
    rel_rows = [r for r in rows if r["cat"] == "R"]
    irr_rows = [r for r in rows if r["cat"] == "I"]
    tri_rows = [r for r in rows if r["cat"] == "T"]
    
    old_tp = sum(1 for r in rel_rows if r["old_pass"])
    new_tp = sum(1 for r in rel_rows if r["new_pass"])
    old_tn_irr = sum(1 for r in irr_rows if not r["old_pass"])
    new_tn_irr = sum(1 for r in irr_rows if not r["new_pass"])
    old_tn_tri = sum(1 for r in tri_rows if not r["old_pass"])
    new_tn_tri = sum(1 for r in tri_rows if not r["new_pass"])
    old_acc = (old_tp + old_tn_irr + old_tn_tri)
    new_acc = (new_tp + new_tn_irr + new_tn_tri)
    
    lines.append("## Overall Accuracy")
    lines.append("")
    lines.append("| Metric | OLD (L2², 41%) | NEW (cosine, 70%) | Winner |")
    lines.append("|--------|---------------|-------------------|--------|")
    lines.append(f"| Relevant passed (recall) | {old_tp}/{len(rel_rows)} = {old_tp/len(rel_rows)*100:.0f}% | {new_tp}/{len(rel_rows)} = {new_tp/len(rel_rows)*100:.0f}% | {'⬅️ OLD' if old_tp > new_tp else '➡️ NEW' if new_tp > old_tp else 'TIE'} |")
    lines.append(f"| Irrelevant rejected | {old_tn_irr}/{len(irr_rows)} = {old_tn_irr/len(irr_rows)*100:.0f}% | {new_tn_irr}/{len(irr_rows)} = {new_tn_irr/len(irr_rows)*100:.0f}% | {'⬅️ OLD' if old_tn_irr > new_tn_irr else '➡️ NEW' if new_tn_irr > old_tn_irr else 'TIE'} |")
    lines.append(f"| Tricky rejected | {old_tn_tri}/{len(tri_rows)} = {old_tn_tri/len(tri_rows)*100:.0f}% | {new_tn_tri}/{len(tri_rows)} = {new_tn_tri/len(tri_rows)*100:.0f}% | {'⬅️ OLD' if old_tn_tri > new_tn_tri else '➡️ NEW' if new_tn_tri > old_tn_tri else 'TIE'} |")
    lines.append(f"| **Overall accuracy** | {old_acc}/{len(rows)} = {old_acc/len(rows)*100:.0f}% | {new_acc}/{len(rows)} = {new_acc/len(rows)*100:.0f}% | {'⬅️ OLD' if old_acc > new_acc else '➡️ NEW' if new_acc > old_acc else 'TIE'} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Per-query tables
    for section_title, section_rows, cat_marker in [
        ("✅ Relevant Queries (Should PASS)", rel_rows, "✅"),
        ("❌ Irrelevant Queries (Should FAIL)", irr_rows, "❌"),
        ("⚠️ Tricky Queries (Hospital-sounding, No FAQ — Should FAIL)", tri_rows, "⚠️"),
    ]:
        lines.append(f"## Per-Query: {section_title}")
        lines.append("")
        lines.append("| # | Query | OLD Score | OLD | OLD Retrieved | NEW Score | NEW | NEW Retrieved | Same? |")
        lines.append("|---|-------|-----------|-----|---------------|-----------|-----|---------------|-------|")
        
        for j, r in enumerate(section_rows):
            q = r["query"]
            old_s = f"{r['old_score']:.1f}%"
            new_s = f"{r['new_score']:.1f}%"
            
            if r["cat"] == "R":
                old_v = "✅ PASS" if r["old_pass"] else "❌ FAIL"
                new_v = "✅ PASS" if r["new_pass"] else "❌ FAIL"
            else:
                old_v = "✅ FAIL" if not r["old_pass"] else "❌ LEAK"
                new_v = "✅ FAIL" if not r["new_pass"] else "❌ LEAK"
            
            same = "✅" if r["old_title"] == r["new_title"] else "⚡ DIFF"
            
            old_t = r["old_title"][:45]
            new_t = r["new_title"][:45]
            
            lines.append(f"| {j+1} | {q} | {old_s} | {old_v} | {old_t} | {new_s} | {new_v} | {new_t} | {same} |")
        
        # Count differences
        diffs = sum(1 for r in section_rows if r["old_title"] != r["new_title"])
        lines.append("")
        lines.append(f"> **Different retrievals**: {diffs}/{len(section_rows)} queries retrieved a different top FAQ between OLD and NEW.")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # Conclusion
    lines.append("## Conclusion")
    lines.append("")
    lines.append("| Aspect | OLD | NEW | Verdict |")
    lines.append("|--------|-----|-----|---------|")
    lines.append(f"| **Overall accuracy** | {old_acc/len(rows)*100:.0f}% | {new_acc/len(rows)*100:.0f}% | {'⬅️ OLD' if old_acc > new_acc else '➡️ NEW'} |")
    lines.append(f"| **Catches relevant** | {old_tp/len(rel_rows)*100:.0f}% | {new_tp/len(rel_rows)*100:.0f}% | {'⬅️ OLD' if old_tp > new_tp else '➡️ NEW'} |")
    lines.append(f"| **Blocks irrelevant** | {old_tn_irr/len(irr_rows)*100:.0f}% | {new_tn_irr/len(irr_rows)*100:.0f}% | {'⬅️ OLD' if old_tn_irr > new_tn_irr else '➡️ NEW'} |")
    lines.append(f"| **Blocks tricky** | {old_tn_tri/len(tri_rows)*100:.0f}% | {new_tn_tri/len(tri_rows)*100:.0f}% | {'⬅️ OLD' if old_tn_tri > new_tn_tri else '➡️ NEW'} |")
    
    total_diffs = sum(1 for r in rows if r["old_title"] != r["new_title"])
    lines.append("")
    lines.append(f"> **Total queries where OLD and NEW retrieved different FAQs**: {total_diffs}/{len(rows)}")

    # Write file
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"✅ Report saved to {REPORT_FILE}")
    
    # Cleanup
    try: client.collections[TEMP_COLLECTION].delete()
    except: pass
    print("🧹 Cleaned up temp collection")


if __name__ == "__main__":
    start = time.time()
    run()
    print(f"\nCompleted in {time.time()-start:.1f}s")
