"""
Extended Benchmark: Short Queries + Old Template Comparison
============================================================
Tests:
  1. Short relevant queries (1-3 words)
  2. Short irrelevant queries
  3. Old template vs New template (re-embeds documents)

Usage:
    $env:PYTHONPATH="."; python scripts/benchmark_extended.py
"""

import time
from typing import List, Tuple
from dataclasses import dataclass

from config import container
from app.services.search_service import SearchService
from app.services.embedding_service import EmbeddingService
from core.tag_manager import TagManager
from core.content_parser import ContentParser


# ============================================================
# SHORT QUERIES
# ============================================================

# Short relevant (1-3 words, should match)
SHORT_RELEVANT = [
    ("obat", "Resep Obat"),
    ("form ed", "form di EMR ED"),
    ("cara input obat", "Resep Obat"),
    ("soap", "SOAP"),
    ("discharge", "Discharge"),
    ("initial assessment", "Initial"),
    ("resep", "Resep"),
    ("call pasien", "Call"),
    ("lab order", "laboratory"),
    ("referral", "Referral"),
    ("mcu", "mcu"),
    ("nurse ipd", "Nurse"),
    ("print lab", "print"),
    ("therapy plan", "Therapy Plan"),
    ("drip obat", "drip"),
]

# Short irrelevant (1-3 words, should NOT match)
SHORT_IRRELEVANT = [
    "nasi padang",
    "sate kambing",
    "bola",
    "cuaca",
    "indonesia",
    "brownies",
    "iphone",
    "motor",
    "tiket",
    "musik",
]

# Short tricky (1-3 words, hospital-sounding but no FAQ)
SHORT_TRICKY = [
    "reset password",
    "booking ok",
    "rawat jalan",
    "jadwal dokter",
    "radiologi",
    "bpjs",
    "shift perawat",
    "transfer pasien",
    "rekam medis",
    "rontgen",
]


@dataclass
class Result:
    query: str
    category: str
    top_score: float
    top_title: str
    method: str


def search_with_task_type(query: str, task_type: str) -> Tuple[float, str]:
    """Run search with specified embedding task type."""
    embedding = container.get_embedding().embed(query, task_type=task_type)
    if not embedding:
        return 0.0, "ERROR"
    
    store = container.get_vector_store()
    raw_results = store.query(query_embedding=embedding, n_results=1)
    
    if not raw_results:
        return 0.0, "NO RESULTS"
    
    top = raw_results[0]
    score = SearchService.calculate_relevance(top.distance)
    title = top.metadata.get("judul", "?")
    return score, title


def search_with_old_template(query: str) -> Tuple[float, str]:
    """
    Simulate old template by embedding query as a 'document' using old format.
    Old format: DOMAIN + DOKUMEN + VARIASI PERTANYAAN USER + ISI KONTEN
    """
    # Old template format for the query (simulating how old system would embed)
    old_format_query = f"""DOMAIN: Unknown
DOKUMEN: {query}
VARIASI PERTANYAAN USER: {query}
ISI KONTEN: {query}"""
    
    embedding = container.get_embedding().embed(old_format_query, task_type="RETRIEVAL_DOCUMENT")
    if not embedding:
        return 0.0, "ERROR"
    
    store = container.get_vector_store()
    raw_results = store.query(query_embedding=embedding, n_results=1)
    
    if not raw_results:
        return 0.0, "NO RESULTS"
    
    top = raw_results[0]
    score = SearchService.calculate_relevance(top.distance)
    title = top.metadata.get("judul", "?")
    return score, title


def run_benchmark():
    results: List[Result] = []
    
    methods = [
        ("asymmetric", "Current (RETRIEVAL_QUERY)", lambda q: search_with_task_type(q, "RETRIEVAL_QUERY")),
        ("symmetric", "Symmetric (RETRIEVAL_DOCUMENT)", lambda q: search_with_task_type(q, "RETRIEVAL_DOCUMENT")),
        ("old_template", "Old Template Format (Simulated)", lambda q: search_with_old_template(q)),
    ]
    
    total = (len(SHORT_RELEVANT) + len(SHORT_IRRELEVANT) + len(SHORT_TRICKY)) * len(methods)
    count = 0
    
    print(f"\n{'='*80}")
    print(f"EXTENDED BENCHMARK: SHORT QUERIES + OLD TEMPLATE")
    print(f"{'='*80}")
    print(f"Queries: {len(SHORT_RELEVANT)} relevant + {len(SHORT_IRRELEVANT)} irrelevant + {len(SHORT_TRICKY)} tricky")
    print(f"Methods: {len(methods)} | Total runs: {total}")
    print(f"{'='*80}\n")
    
    for method_key, method_name, search_fn in methods:
        print(f"\n--- {method_name} ---\n")
        
        for query, expected in SHORT_RELEVANT:
            count += 1
            print(f"  [{count}/{total}] {query:<25}", end="", flush=True)
            score, title = search_fn(query)
            matched = expected.lower() in title.lower()
            marker = "✅" if matched else "⚠️"
            print(f" → {score:.1f}% {marker} {title[:35]}")
            results.append(Result(query, "RELEVANT", score, title, method_name))
        
        for query in SHORT_IRRELEVANT:
            count += 1
            print(f"  [{count}/{total}] {query:<25}", end="", flush=True)
            score, title = search_fn(query)
            print(f" → {score:.1f}% ❌ {title[:35]}")
            results.append(Result(query, "IRRELEVANT", score, title, method_name))
        
        for query in SHORT_TRICKY:
            count += 1
            print(f"  [{count}/{total}] {query:<25}", end="", flush=True)
            score, title = search_fn(query)
            print(f" → {score:.1f}% ❌ {title[:35]}")
            results.append(Result(query, "TRICKY", score, title, method_name))
    
    # ============================================================
    # ANALYSIS
    # ============================================================
    print(f"\n\n{'='*80}")
    print("ANALYSIS: SHORT QUERIES")
    print(f"{'='*80}")
    
    for method_name in [m[1] for m in methods]:
        mr = [r for r in results if r.method == method_name]
        
        rel = [r.top_score for r in mr if r.category == "RELEVANT"]
        irr = [r.top_score for r in mr if r.category == "IRRELEVANT"]
        tri = [r.top_score for r in mr if r.category == "TRICKY"]
        
        rel_avg, rel_min, rel_max = sum(rel)/len(rel), min(rel), max(rel)
        irr_avg, irr_min, irr_max = sum(irr)/len(irr), min(irr), max(irr)
        tri_avg, tri_min, tri_max = sum(tri)/len(tri), min(tri), max(tri)
        
        noise_max = max(irr_max, tri_max)
        gap = rel_min - noise_max
        
        print(f"\n--- {method_name} ---")
        print(f"  RELEVANT   : avg={rel_avg:.1f}%  min={rel_min:.1f}%  max={rel_max:.1f}%")
        print(f"  IRRELEVANT : avg={irr_avg:.1f}%  min={irr_min:.1f}%  max={irr_max:.1f}%")
        print(f"  TRICKY     : avg={tri_avg:.1f}%  min={tri_min:.1f}%  max={tri_max:.1f}%")
        print(f"  GAP (rel_min - noise_max): {gap:.1f}%")
        
        if gap > 0:
            threshold = (rel_min + noise_max) / 2
            print(f"  ✅ CLEAN SEPARATION! Suggested threshold: {threshold:.0f}%")
        else:
            overlap_pct = abs(gap) / (rel_max - irr_min) * 100 if (rel_max - irr_min) > 0 else 0
            print(f"  ⚠️  OVERLAP of {abs(gap):.1f}% — agent mode recommended")

    # ============================================================
    # COMPARISON TABLE
    # ============================================================
    print(f"\n\n{'='*80}")
    print("COMPARISON: ALL METHODS SIDE BY SIDE")
    print(f"{'='*80}")
    
    print(f"\n{'Query':<28} ", end="")
    for _, method_name, _ in methods:
        short_name = method_name.split("(")[0].strip()[:12]
        print(f"{'|':>1} {short_name:>12}", end="")
    print()
    print(f"{'─'*28} ", end="")
    for _ in methods:
        print(f"{'|':>1} {'─'*12}", end="")
    print()
    
    all_queries = (
        [(q, "R") for q, _ in SHORT_RELEVANT] +
        [(q, "I") for q in SHORT_IRRELEVANT] +
        [(q, "T") for q in SHORT_TRICKY]
    )
    
    for query, cat in all_queries:
        marker = {"R": "✅", "I": "❌", "T": "⚠️"}[cat]
        print(f"{marker} {query:<25} ", end="")
        for _, method_name, _ in methods:
            score = next((r.top_score for r in results 
                         if r.method == method_name and r.query == query), 0)
            print(f"| {score:>10.1f}%", end="")
        print()


if __name__ == "__main__":
    start = time.time()
    run_benchmark()
    elapsed = time.time() - start
    print(f"\n\nBenchmark completed in {elapsed:.1f}s")
