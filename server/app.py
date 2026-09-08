from dotenv import load_dotenv
load_dotenv()

"""
FastAPI Server for Group Chat Semantic Search Engine.
Provides REST endpoints for hybrid search, conversation context retrieval,
conversational AI chat with citations via OpenRouter, benchmark execution, and corpus statistics.
"""

import os
import sys
import json
import time
import httpx
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

PROJECT_ROOT = r"D:\group-chat-search"
sys.path.insert(0, PROJECT_ROOT)

from engine.search import ChatSearchEngine

app = FastAPI(
    title="Search a Group Chat Properly",
    description="Context-Aware Semantic Search Engine & Copilot for Code-Mixed Hinglish Group Chats",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CORPUS_PATH = os.path.join(PROJECT_ROOT, "dataset", "chat_corpus.json")
EMBEDDINGS_PATH = os.path.join(PROJECT_ROOT, "engine", "embeddings.npy")
BENCHMARK_PATH = os.path.join(PROJECT_ROOT, "dataset", "benchmark_queries.json")
WEB_DIR = os.path.join(PROJECT_ROOT, "web")

# Search engine singleton
engine: Optional[ChatSearchEngine] = None

def get_engine() -> ChatSearchEngine:
    global engine
    if engine is None:
        engine = ChatSearchEngine(CORPUS_PATH, EMBEDDINGS_PATH)
    return engine

# Pydantic models
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 10
    context_radius: Optional[int] = 3
    sender_filter: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None

class ChatRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


@app.get("/api/health")
async def health_check():
    eng = get_engine()
    return {
        "status": "online",
        "corpus_loaded": len(eng.corpus),
        "embeddings_ready": eng.embeddings is not None
    }


@app.post("/api/search")
async def search_endpoint(req: SearchRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    eng = get_engine()
    try:
        results = eng.search(
            query=req.query,
            top_k=req.top_k,
            context_radius=req.context_radius,
            explicit_sender=req.sender_filter,
            explicit_start=req.date_start,
            explicit_end=req.date_end
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/context/{message_id}")
async def context_endpoint(message_id: int, radius: int = 5):
    eng = get_engine()
    context_data = eng.get_context(message_id=message_id, radius=radius)
    if "error" in context_data:
        raise HTTPException(status_code=404, detail=context_data["error"])
    return context_data


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    eng = get_engine()

    # Retrieve top relevant chat messages
    search_res = eng.search(req.query, top_k=req.top_k, context_radius=2)
    results = search_res.get("results", [])

    if not results:
        return {
            "answer": "I couldn't find any relevant conversation snippets discussing that topic in the group chat.",
            "cited_messages": [],
            "query_analysis": search_res.get("query_analysis", {})
        }

    # Format context for prompt
    context_blocks = []
    cited_messages = []
    for r in results:
        m = r["message"]
        cited_messages.append(m)
        surrounding = " ".join([f"{c['sender']}: {c['text']}" for c in r.get("context", [])])
        context_blocks.append(f"[Message #{m['id']}] Date: {m['timestamp']} | Sender: {m['sender']}\nMessage: \"{m['text']}\"\nSurrounding conversation: {surrounding}\n")

    context_prompt_text = "\n---\n".join(context_blocks)

    api_key = os.environ.get("OPENROUTER_API_KEY", "")

    # Attempt LLM synthesis via OpenRouter
    if api_key:
        system_prompt = (
            "You are an intelligent group chat assistant. Answer the user's question directly, accurately, "
            "and concisely based strictly on the retrieved chat snippets. "
            "You MUST cite exact message IDs like [#123] whenever making a statement. "
            "Explain any Hinglish slang if helpful. Never hallucinate or assume facts not present in the chat."
        )
        user_prompt = f"Question: {req.query}\n\nGroup Chat Context:\n{context_prompt_text}\n\nAnswer:"

        payload = {
            "model": "google/gemma-3n-e4b-it:free",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 500
        }

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://127.0.0.1:8000",
                        "X-Title": "Proper Group Chat Search"
                    },
                    json=payload
                )
                if resp.status_code == 200:
                    data = resp.json()
                    answer = data["choices"][0]["message"]["content"]
                    return {
                        "answer": answer,
                        "cited_messages": cited_messages,
                        "query_analysis": search_res.get("query_analysis", {})
                    }
                else:
                    print(f"OpenRouter response code: {resp.status_code}, falling back to local synthesis")
        except Exception as err:
            print(f"OpenRouter call failed: {err}, using fallback synthesis")

    # Local Fallback Synthesizer
    top_m = results[0]["message"]
    fallback_answer = (
        f"Based on the conversation records, **{top_m['sender']}** stated on {top_m['timestamp'][:10]}: "
        f"\"{top_m['text']}\" [#{top_m['id']}]. "
    )
    if len(results) > 1:
        second_m = results[1]["message"]
        fallback_answer += f"Additionally, **{second_m['sender']}** noted: \"{second_m['text']}\" [#{second_m['id']}]."

    return {
        "answer": fallback_answer,
        "cited_messages": cited_messages,
        "query_analysis": search_res.get("query_analysis", {})
    }


@app.get("/api/benchmark")
async def run_benchmark():
    eng = get_engine()

    if not os.path.exists(BENCHMARK_PATH):
        raise HTTPException(status_code=404, detail="Benchmark queries file not found.")

    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        queries = json.load(f)

    per_query_results = []
    hit_1 = 0
    hit_3 = 0
    hit_5 = 0
    reciprocal_ranks = []
    latencies = []

    zero_overlap_total = 0
    zero_overlap_hit_3 = 0

    for q in queries:
        qid = q["id"]
        qtext = q["query"]
        is_zero = q.get("zero_lexical_overlap", False)

        # Multi-target + Proximity resolution
        target_ids = q.get("answer_message_ids") or ([q["answer_message_id"]] if "answer_message_id" in q else [])
        proximity = q.get("accept_thread_proximity", 0)
        valid_ids = set(target_ids)

        if proximity > 0:
            for tid in target_ids:
                if tid in eng.id_to_idx:
                    center = eng.id_to_idx[tid]
                    for offset in range(-proximity, proximity + 1):
                        n_idx = center + offset
                        if 0 <= n_idx < len(eng.corpus):
                            valid_ids.add(eng.corpus[n_idx]["id"])

        t_start = time.time()
        res = eng.search(qtext, top_k=5, context_radius=3)
        latency = (time.time() - t_start) * 1000
        latencies.append(latency)

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

        if is_zero:
            zero_overlap_total += 1
            if rank > 0 and rank <= 3:
                zero_overlap_hit_3 += 1

        primary_target_id = target_ids[0] if target_ids else None
        target_message = eng.corpus[eng.id_to_idx[primary_target_id]] if (primary_target_id and primary_target_id in eng.id_to_idx) else None

        per_query_results.append({
            "id": qid,
            "query": qtext,
            "query_type": q.get("query_type", "semantic"),
            "zero_lexical_overlap": is_zero,
            "target_message_id": primary_target_id,
            "target_ids": target_ids,
            "matched_target_id": matched_target_id,
            "target_message": target_message,
            "retrieved_ids": retrieved_ids,
            "rank": rank,
            "passed": (rank > 0 and rank <= 3),
            "latency_ms": round(latency, 2)
        })

    n = len(queries)
    metrics = {
        "total_queries": n,
        "hit_at_1": round(hit_1 / n * 100, 1),
        "hit_at_3": round(hit_3 / n * 100, 1),
        "hit_at_5": round(hit_5 / n * 100, 1),
        "mrr": round(float(sum(reciprocal_ranks) / n), 3),
        "zero_lexical_total": zero_overlap_total,
        "zero_lexical_hit_at_3": round(zero_overlap_hit_3 / max(1, zero_overlap_total) * 100, 1),
        "avg_latency_ms": round(float(sum(latencies) / n), 2)
    }

    return {
        "metrics": metrics,
        "queries": per_query_results
    }


@app.get("/api/stats")
async def stats_endpoint():
    eng = get_engine()
    senders = {}
    for m in eng.corpus:
        s = m["sender"]
        senders[s] = senders.get(s, 0) + 1

    return {
        "total_messages": len(eng.corpus),
        "start_date": eng.corpus[0]["timestamp"],
        "end_date": eng.corpus[-1]["timestamp"],
        "participant_counts": senders,
        "major_threads": [
            {"name": "Himachal Road Trip Planning (Manali)", "month": "June 2024", "outcome": "Dates locked June 14-18, Cottage booked, Scorpio self-drive, 8.5k budget cap"},
            {"name": "Indiranagar 3BHK Flat Hunting & Moving", "month": "July-August 2024", "outcome": "Ramesh broker, 54k rent split 3-ways, 2.5L deposit, moving Aug 1"},
            {"name": "ChatPulse AI Hackathon Project", "month": "Sept-Oct 2024", "outcome": "FastAPI + React stack, Sept 25 deck deadline, demo video, 2nd place win"}
        ]
    }

# Serve web static assets
if os.path.exists(WEB_DIR):
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
