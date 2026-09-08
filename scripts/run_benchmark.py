"""
Standalone CLI Benchmark Evaluation Suite for 'Search a Group Chat Properly'.
Evaluates 40 gold-standard queries across Semantic, Attributed, and Temporal categories.
Features production-grade multi-target and thread-proximity evaluation.
Validates zero-lexical overlap comprehension, Hit@1, Hit@3, Hit@5, MRR, and latency.
"""

import os
import sys
import json
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from engine.search import ChatSearchEngine

CORPUS_PATH = os.path.join(PROJECT_ROOT, "dataset", "chat_corpus.json")
EMBEDDINGS_PATH = os.path.join(PROJECT_ROOT, "engine", "embeddings.npy")
BENCHMARK_PATH = os.path.join(PROJECT_ROOT, "dataset", "benchmark_queries.json")
RESULTS_PATH = os.path.join(PROJECT_ROOT, "scripts", "benchmark_results.json")


def run_benchmark():
    print("=" * 80)
    print(" SEARCH A GROUP CHAT PROPERLY -- 40-QUERY BENCHMARK EVALUATION")
    print("=" * 80)

    if not os.path.exists(EMBEDDINGS_PATH):
        print(f"Error: Embeddings not found at {EMBEDDINGS_PATH}. Please run build_index.py first.")
        sys.exit(1)

    print("Initializing ChatSearchEngine...")
    t0 = time.time()
    engine = ChatSearchEngine(CORPUS_PATH, EMBEDDINGS_PATH)
    print(f"Engine ready in {time.time() - t0:.2f}s\n")

    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        queries = json.load(f)

    print(f"Loaded {len(queries)} gold-standard benchmark queries.\n")

    hit_1 = 0
    hit_3 = 0
    hit_5 = 0
    reciprocal_ranks = []
    latencies = []

    zero_queries = []
    all_results = []

    print(f"{'#':<3} | {'Type':<12} | {'Zero':<6} | {'Rank':<6} | {'Lat(ms)':<8} | {'Query'}")
    print("-" * 80)

    for q in queries:
        qid = q["id"]
        qtext = q["query"]
        qtype = q.get("query_type", "semantic")
        is_zero = q.get("zero_lexical_overlap", False)

        # Multi-target + Proximity resolution
        target_ids = q.get("answer_message_ids") or ([q["answer_message_id"]] if "answer_message_id" in q else [])
        proximity = q.get("accept_thread_proximity", 0)
        valid_ids = set(target_ids)

        if proximity > 0:
            for tid in target_ids:
                if tid in engine.id_to_idx:
                    center = engine.id_to_idx[tid]
                    for offset in range(-proximity, proximity + 1):
                        n_idx = center + offset
                        if 0 <= n_idx < len(engine.corpus):
                            valid_ids.add(engine.corpus[n_idx]["id"])

        t_start = time.time()
        res = engine.search(qtext, top_k=5, context_radius=3)
        lat = (time.time() - t_start) * 1000
        latencies.append(lat)

        retrieved_ids = [r["message"]["id"] for r in res.get("results", [])]

        rank = 0
        matched_target_id = None
        for i, rid in enumerate(retrieved_ids):
            if rid in valid_ids:
                rank = i + 1
                matched_target_id = rid
                reciprocal_ranks.append(1.0 / rank)
                break
        else:
            reciprocal_ranks.append(0.0)

        if rank == 1:
            hit_1 += 1
        if rank > 0 and rank <= 3:
            hit_3 += 1
        if rank > 0 and rank <= 5:
            hit_5 += 1

        status_str = f"#{rank}" if rank > 0 else "MISS"
        zero_str = "YES" if is_zero else "-"

        print(f"Q{qid:<2} | {qtype:<12} | {zero_str:<6} | {status_str:<6} | {lat:<8.1f} | {qtext[:36]}")

        primary_target_id = target_ids[0] if target_ids else None
        target_msg = engine.corpus[engine.id_to_idx[primary_target_id]]["text"] if (primary_target_id and primary_target_id in engine.id_to_idx) else ""

        query_res = {
            "id": qid,
            "query": qtext,
            "query_type": qtype,
            "zero_lexical_overlap": is_zero,
            "target_ids": target_ids,
            "matched_target_id": matched_target_id,
            "target_text": target_msg,
            "rank": rank,
            "retrieved_ids": retrieved_ids,
            "passed": (rank > 0 and rank <= 3),
            "latency_ms": round(lat, 2)
        }
        all_results.append(query_res)
        if is_zero:
            zero_queries.append(query_res)

    total = len(queries)
    zero_total = len(zero_queries)
    zero_hit_3 = sum(1 for z in zero_queries if z["rank"] > 0 and z["rank"] <= 3)

    mrr = sum(reciprocal_ranks) / total
    avg_lat = sum(latencies) / total

    print("\n" + "=" * 80)
    print(" BENCHMARK ACCURACY SCORECARD")
    print("=" * 80)
    print(f"Total Test Queries:               {total}")
    print(f"Hit@1 Accuracy (Rank #1):         {hit_1}/{total} ({hit_1/total*100:.1f}%)")
    print(f"Hit@3 Accuracy (Top 3):           {hit_3}/{total} ({hit_3/total*100:.1f}%)")
    print(f"Hit@5 Accuracy (Top 5):           {hit_5}/{total} ({hit_5/total*100:.1f}%)")
    print(f"Mean Reciprocal Rank (MRR):       {mrr:.3f}")
    print(f"Average Search Latency:           {avg_lat:.2f} ms")
    print("-" * 80)
    print(f"ZERO-LEXICAL OVERLAP ACCURACY:    {zero_hit_3}/{zero_total} ({zero_hit_3/zero_total*100:.1f}%)")
    print("=" * 80)

    print("\nDetailed Breakdown of 10 Zero-Lexical Overlap Test Cases:")
    for z in zero_queries:
        pass_symbol = "[PASS]" if z["rank"] > 0 and z["rank"] <= 3 else "[FAIL]"
        print(f"\n[Query #{z['id']}] {pass_symbol} (Rank #{z['rank']})")
        print(f"  English Query: \"{z['query']}\"")
        print(f"  Hinglish Target: \"{z['target_text']}\"")

    # Save to JSON
    summary = {
        "metrics": {
            "total_queries": total,
            "hit_at_1_pct": round(hit_1 / total * 100, 1),
            "hit_at_3_pct": round(hit_3 / total * 100, 1),
            "hit_at_5_pct": round(hit_5 / total * 100, 1),
            "mrr": round(mrr, 3),
            "zero_lexical_total": zero_total,
            "zero_lexical_hit_at_3_pct": round(zero_hit_3 / max(1, zero_total) * 100, 1),
            "avg_latency_ms": round(avg_lat, 2)
        },
        "query_results": all_results
    }
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nBenchmark results saved to: {RESULTS_PATH}")


if __name__ == "__main__":
    run_benchmark()
