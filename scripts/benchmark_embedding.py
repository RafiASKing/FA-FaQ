"""
Embedding Benchmark Test
========================
Compares retrieval quality between:
  - Method A (Current): RETRIEVAL_QUERY (asymmetric)
  - Method B (Old): RETRIEVAL_DOCUMENT (symmetric)

Tests 3 query categories:
  1. RELEVANT  - queries that SHOULD match a FAQ
  2. IRRELEVANT - obviously off-topic queries
  3. TRICKY    - hospital-sounding but NO matching FAQ exists

Usage:
    $env:PYTHONPATH="."; python scripts/benchmark_embedding.py
"""

import time
from typing import List, Tuple
from dataclasses import dataclass

from config import container
from app.services.search_service import SearchService


# ============================================================
# TEST QUERIES
# ============================================================

# Category 1: RELEVANT - should match existing FAQs
# Format: (query, expected_faq_title_substring)
RELEVANT_QUERIES = [
    # Direct matches
    ("tombol call pasien saya abu-abu gabisa diklik", "Call"),
    ("gabisa login di hp nurse ipd", "Nurse Tidak Bisa Mengakses"),
    ("cara nambah resep obat di soap", "Resep Obat"),
    ("form apa aja yang belum ada di emr ed?", "form di EMR ED"),
    ("cara print order lab di igd", "print order laboratory"),
    ("bisa gak edit obat di farmasi ed?", "Mengedit Obat"),
    ("gimana bikin initial assessment pasien baru?", "Initial"),
    ("data yang wajib diisi di soap itu apa aja?", "mandatory"),
    ("mau liat list pasien besok jadwal saya gimana?", "list pasien"),
    ("bisa gak order obat sebelum asesmen perawat?", "order obat sebelum"),
    
    # Paraphrased / casual language
    ("kenapa discharge pasien error gabisa?", "Discharge"),
    ("obat drip bisa diresepkan gak?", "drip"),
    ("jam datang pasien itu tercatat kapan sih?", "jam datang"),
    ("cashier mau print form lab dari igd bisa gak?", "cashier"),
    ("template soap rehab kok gak ada therapy plan?", "Therapy Plan"),
    
    # Keyword-style queries
    ("referral konsultasi ipd", "Referral"),
    ("revisi mr koding", "revisi MR"),
    ("drugs outside formularium", "Formularium"),
    ("bni life mcu", "bni life"),
    ("ncp ansietas nyeri", "NCP"),
]

# Category 2: IRRELEVANT - obviously off-topic
IRRELEVANT_QUERIES = [
    "makan nasi padang yok",
    "sate kambing enak banget",
    "afiif ahmad ramadhan suka apa?",
    "siapa presiden indonesia sekarang?",
    "harga tiket pesawat jakarta bali",
    "cara masak rendang padang",
    "manchester united menang berapa?",
    "cuaca hari ini di jakarta",
    "resep kue brownies coklat",
    "berapa harga iphone 16 pro max?",
]

# Category 3: TRICKY - hospital-sounding but NO FAQ exists
TRICKY_QUERIES = [
    "cara reset password emr saya lupa",            # No FAQ about password reset
    "bagaimana cara transfer pasien antar ruangan?", # No FAQ about patient transfer
    "dimana menu untuk input hasil radiologi?",      # No FAQ about radiology input
    "cara bikin surat rujukan BPJS",                 # No FAQ about BPJS referral
    "gimana caranya booking ruang operasi?",          # No FAQ about OR booking
    "bagaimana input hasil laboratorium di emr?",    # No FAQ about lab result input
    "cara membatalkan order farmasi yang sudah masuk", # No FAQ about pharmacy cancel
    "apakah bisa mendaftarkan pasien BPJS online?",  # No FAQ about BPJS registration
    "cara akses emr dari laptop pribadi?",           # No FAQ about personal device access
    "bagaimana mengganti jadwal shift perawat?",     # No FAQ about shift scheduling
]


@dataclass
class BenchmarkResult:
    query: str
    category: str
    top_score: float
    top_title: str
    method: str


def run_search_with_method(query: str, task_type: str) -> Tuple[float, str]:
    """
    Run a single search query with specified task type.
    Returns (top_score, top_title).
    """
    # Generate embedding with specified task type
    embedding = container.get_embedding().embed(query, task_type=task_type)
    
    if not embedding:
        return 0.0, "ERROR"
    
    # Query vector store
    store = container.get_vector_store()
    raw_results = store.query(
        query_embedding=embedding,
        n_results=3,
    )
    
    if not raw_results:
        return 0.0, "NO RESULTS"
    
    # Get top result
    top = raw_results[0]
    score = SearchService.calculate_relevance(top.distance)
    title = top.metadata.get("judul", "?")
    
    return score, title


def run_benchmark():
    """Run the full benchmark."""
    results: List[BenchmarkResult] = []
    
    methods = [
        ("RETRIEVAL_QUERY", "Asymmetric (Current)"),
        ("RETRIEVAL_DOCUMENT", "Symmetric (Old)"),
    ]
    
    total_queries = len(RELEVANT_QUERIES) + len(IRRELEVANT_QUERIES) + len(TRICKY_QUERIES)
    total_runs = total_queries * len(methods)
    run_count = 0
    
    print(f"\n{'='*80}")
    print(f"EMBEDDING BENCHMARK TEST")
    print(f"{'='*80}")
    print(f"Total queries: {total_queries} | Methods: {len(methods)} | Total runs: {total_runs}")
    print(f"{'='*80}\n")
    
    for task_type, method_name in methods:
        print(f"\n--- Method: {method_name} ({task_type}) ---\n")
        
        # Relevant queries
        for query, expected in RELEVANT_QUERIES:
            run_count += 1
            print(f"  [{run_count}/{total_runs}] Testing: {query[:50]}...", end="", flush=True)
            score, title = run_search_with_method(query, task_type)
            print(f" → {score:.1f}% ({title[:30]})")
            results.append(BenchmarkResult(query, "RELEVANT", score, title, method_name))
        
        # Irrelevant queries
        for query in IRRELEVANT_QUERIES:
            run_count += 1
            print(f"  [{run_count}/{total_runs}] Testing: {query[:50]}...", end="", flush=True)
            score, title = run_search_with_method(query, task_type)
            print(f" → {score:.1f}% ({title[:30]})")
            results.append(BenchmarkResult(query, "IRRELEVANT", score, title, method_name))
        
        # Tricky queries
        for query in TRICKY_QUERIES:
            run_count += 1
            print(f"  [{run_count}/{total_runs}] Testing: {query[:50]}...", end="", flush=True)
            score, title = run_search_with_method(query, task_type)
            print(f" → {score:.1f}% ({title[:30]})")
            results.append(BenchmarkResult(query, "TRICKY", score, title, method_name))
    
    # ============================================================
    # ANALYSIS
    # ============================================================
    print(f"\n\n{'='*80}")
    print("ANALYSIS")
    print(f"{'='*80}")
    
    for method_name in [m[1] for m in methods]:
        method_results = [r for r in results if r.method == method_name]
        
        relevant = [r.top_score for r in method_results if r.category == "RELEVANT"]
        irrelevant = [r.top_score for r in method_results if r.category == "IRRELEVANT"]
        tricky = [r.top_score for r in method_results if r.category == "TRICKY"]
        
        relevant_avg = sum(relevant) / len(relevant) if relevant else 0
        relevant_min = min(relevant) if relevant else 0
        relevant_max = max(relevant) if relevant else 0
        
        irrelevant_avg = sum(irrelevant) / len(irrelevant) if irrelevant else 0
        irrelevant_min = min(irrelevant) if irrelevant else 0
        irrelevant_max = max(irrelevant) if irrelevant else 0
        
        tricky_avg = sum(tricky) / len(tricky) if tricky else 0
        tricky_min = min(tricky) if tricky else 0
        tricky_max = max(tricky) if tricky else 0
        
        gap = relevant_min - max(irrelevant_max, tricky_max)
        
        print(f"\n--- {method_name} ---")
        print(f"  RELEVANT   : avg={relevant_avg:.1f}%  min={relevant_min:.1f}%  max={relevant_max:.1f}%")
        print(f"  IRRELEVANT : avg={irrelevant_avg:.1f}%  min={irrelevant_min:.1f}%  max={irrelevant_max:.1f}%")
        print(f"  TRICKY     : avg={tricky_avg:.1f}%  min={tricky_min:.1f}%  max={tricky_max:.1f}%")
        print(f"  GAP (relevant_min - max_noise): {gap:.1f}%")
        
        if gap > 0:
            suggested_threshold = (relevant_min + max(irrelevant_max, tricky_max)) / 2
            print(f"  ✅ CLEAN SEPARATION! Suggested threshold: {suggested_threshold:.0f}%")
        else:
            print(f"  ⚠️  OVERLAP detected — threshold alone won't work, agent mode needed")
    
    # ============================================================
    # DISTRIBUTION CHART (ASCII)
    # ============================================================
    print(f"\n\n{'='*80}")
    print("SCORE DISTRIBUTION (ASCII)")
    print(f"{'='*80}")
    
    for method_name in [m[1] for m in methods]:
        method_results = [r for r in results if r.method == method_name]
        print(f"\n--- {method_name} ---")
        
        # Create buckets: 0-9, 10-19, ..., 90-100
        buckets = {i: {"R": 0, "I": 0, "T": 0} for i in range(0, 101, 5)}
        
        for r in method_results:
            bucket = int(r.top_score // 5) * 5
            bucket = min(bucket, 95)
            cat_key = r.category[0]  # R, I, T
            buckets[bucket][cat_key] += 1
        
        print(f"  {'Score':>6}  Relevant(R) | Irrelevant(I) | Tricky(T)")
        print(f"  {'─'*55}")
        
        for bucket in sorted(buckets.keys(), reverse=True):
            counts = buckets[bucket]
            total = sum(counts.values())
            if total == 0:
                continue
            
            bar_r = "R" * counts["R"]
            bar_i = "I" * counts["I"]
            bar_t = "T" * counts["T"]
            
            print(f"  {bucket:>3}-{bucket+4:<3} {bar_r}{bar_i}{bar_t}")
    
    # ============================================================
    # DETAILED RESULTS TABLE
    # ============================================================
    print(f"\n\n{'='*80}")
    print("DETAILED RESULTS")
    print(f"{'='*80}")
    
    for method_name in [m[1] for m in methods]:
        method_results = [r for r in results if r.method == method_name]
        print(f"\n--- {method_name} ---")
        
        for cat in ["RELEVANT", "IRRELEVANT", "TRICKY"]:
            cat_results = sorted(
                [r for r in method_results if r.category == cat],
                key=lambda x: x.top_score,
                reverse=True
            )
            print(f"\n  {cat}:")
            for r in cat_results:
                marker = "✅" if cat == "RELEVANT" else "❌"
                print(f"    {marker} {r.top_score:5.1f}%  {r.query[:45]:<47} → {r.top_title[:30]}")


if __name__ == "__main__":
    start = time.time()
    run_benchmark()
    elapsed = time.time() - start
    print(f"\n\nBenchmark completed in {elapsed:.1f}s")
