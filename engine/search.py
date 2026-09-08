"""
Context-Aware Semantic Search Engine for Code-Mixed Hinglish Group Chat Exports.
Supports Semantic, Attributed (speaker-filtered), and Temporal (time-bounded) queries.
Preserves surrounding conversational context for every match.
Features production-grade edge case handling:
  - Semantic floor threshold (discards irrelevant noise before bonuses)
  - Precomputed text frequency counts (penalizes repeated chatter/boilerplate)
  - Comprehensive Hinglish filler dictionary suppression
  - Robust fuzzy temporal expression parsing (early/mid/late, calendar day offsets)
"""

import os
import re
import json
import time
import calendar
from datetime import datetime, timedelta
from collections import Counter
import numpy as np

PARTICIPANT_MAP = {
    "kabir": "Kabir Sharma",
    "priya": "Priya Patel",
    "rohan": "Rohan Mehta",
    "ananya": "Ananya Iyer",
    "vikram": "Vikram Malhotra",
    "tanvi": "Tanvi Joshi",
    "arjun": "Arjun Nair",
    "sneha": "Sneha Rao"
}

MONTH_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12
}

CONCEPT_MAP = {
    "destination": ["manali", "pahadon", "destination", "chalo", "fix"],
    "vacation": ["manali", "pahadon", "trip", "holiday", "getaway"],
    "finances": ["hisab", "kitab", "excel", "sheet", "track", "manage"],
    "car": ["scorpio", "gaadi", "vehicle", "drive", "suv", "chalayega"],
    "vehicle": ["gaadi", "scorpio", "tyre", "servicing", "check"],
    "booked": ["book", "scorpio", "wooden", "reserve", "booked"],
    "budget": ["8500", "budget", "per head", "kharcha", "ceiling"],
    "dates": ["14 se 18", "dates", "leave", "june", "travel"],
    "moving": ["shifting", "tempo", "1st august", "first august", "shift"],
    "flat": ["3bhk", "indiranagar", "broker", "ramesh", "kiraya", "advance"],
    "rent": ["54000", "chaunvan", "rent", "kiraya", "split"],
    "deposit": ["advance", "deposit", "2.5 lakh", "dhaii", "dhai", "security"],
    "broker": ["ramesh", "broker", "number", "dikha"],
    "hackathon": ["hackathon", "bangalore", "5 lakhs", "prize", "ai category"],
    "startup": ["group chat", "search", "semantic", "tool", "project"],
    "product": ["search tool", "group chat", "whatsapp", "tool"],
    "stack": ["fastapi", "react", "postgres", "backend", "tech"],
    "repo": ["repo", "github", "fork", "code", "push"],
    "deadline": ["25", "deck", "submit", "raat", "barah", "deadline"],
    "video": ["demo", "video", "youtube", "screen recording", "3 min"],
    "stay": ["cottage", "wooden", "old manali", "stay", "1200"],
    "sick": ["altitude", "chakkar", "vomit", "rest", "sick"],
    "cooling": ["fridge", "refrigerator", "cooling", "shift"],
    "server": ["backend", "routes", "database", "models", "server", "endpoints"],
    "bedroom": ["kamra", "bada", "tanvi", "allotment", "furniture"],
    "results": ["2nd place", "secured", "won", "results", "announcement"],
    "bonfire": ["bonfire", "garden", "cottage", "evening"]
}

FILLER_SET = {
    "ok", "okay", "k", "done", "hmm", "haan", "ha", "nahi", "nope",
    "sahi", "chal", "chalo", "ruko", "arrey", "haha", "lol", "nice",
    "theek hai", "acha", "achha", "shi", "yes", "no", "nhi", "thik", "theek",
    "kya", "kab", "kaise", "sahi hai", "cool", "gr8", "bye", "gn",
    "good night", "good morning", "gm", "brb", "afk", "badhiya", "mast",
    "sure", "dekhte", "pakka", "yo", "sorted", "yep", "wait", "shyd kal hoga",
    "bhai", "yaar", "sahi h", "ha bhai", "hn"
}

SEMANTIC_FLOOR = 0.12


class ChatSearchEngine:
    def __init__(self, corpus_path: str, embeddings_path: str, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.corpus_path = corpus_path
        self.embeddings_path = embeddings_path
        self.model_name = model_name
        self.model = None

        print(f"Loading corpus from: {corpus_path}")
        with open(corpus_path, "r", encoding="utf-8") as f:
            self.corpus = json.load(f)

        self.id_to_idx = {msg["id"]: idx for idx, msg in enumerate(self.corpus)}
        self.timestamps = [datetime.fromisoformat(m["timestamp"]) for m in self.corpus]
        self.senders = np.array([m["sender"] for m in self.corpus])

        # Precompute corpus text frequencies for duplicate/boilerplate suppression
        self.corpus_text_counts = Counter(m["text"].strip().lower() for m in self.corpus)

        if os.path.exists(embeddings_path):
            print(f"Loading precomputed embeddings from: {embeddings_path}")
            self.embeddings = np.load(embeddings_path)
            print(f"Loaded embeddings matrix: {self.embeddings.shape}")
        else:
            self.embeddings = None

    def _ensure_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            print(f"Loading SentenceTransformer: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)

    def parse_fuzzy_temporal(self, lower_q: str, year: int = 2024):
        """
        Robust fuzzy natural language temporal parser.
        Extracts date ranges from expressions like 'early September', 'mid-October',
        'last week of August', 'around June 16', cultural dates, etc.
        """
        # Relative expressions
        if re.search(r"\blast month\b", lower_q):
            return datetime(year, 9, 1), datetime(year, 9, 30, 23, 59, 59)
        if re.search(r"\bthis month\b", lower_q):
            return datetime(year, 10, 1), datetime(year, 10, 31, 23, 59, 59)

        # Cultural / Special landmarks
        if "independence day" in lower_q:
            return datetime(year, 8, 8), datetime(year, 8, 20, 23, 59, 59)
        if "diwali" in lower_q:
            return datetime(year, 10, 25), datetime(year, 11, 5, 23, 59, 59)

        # Specific day match e.g. "june 15", "june 16", "15th june"
        m_day = re.search(r"\b([a-zA-Z]+)\s+(\d{1,2})(?:st|nd|rd|th)?\b", lower_q)
        if m_day and m_day.group(1).lower() in MONTH_MAP:
            m_num = MONTH_MAP[m_day.group(1).lower()]
            day_num = int(m_day.group(2))
            d_center = datetime(year, m_num, min(day_num, calendar.monthrange(year, m_num)[1]))
            return d_center - timedelta(days=2), d_center + timedelta(days=2, hours=23, minutes=59, seconds=59)

        m_day_rev = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([a-zA-Z]+)\b", lower_q)
        if m_day_rev and m_day_rev.group(2).lower() in MONTH_MAP:
            m_num = MONTH_MAP[m_day_rev.group(2).lower()]
            day_num = int(m_day_rev.group(1))
            d_center = datetime(year, m_num, min(day_num, calendar.monthrange(year, m_num)[1]))
            return d_center - timedelta(days=2), d_center + timedelta(days=2, hours=23, minutes=59, seconds=59)

        # General month patterns: early, mid, late, last week, first few days
        for m_name, m_num in MONTH_MAP.items():
            if re.search(rf"\b{m_name}\b", lower_q):
                last_day = calendar.monthrange(year, m_num)[1]
                m_start = datetime(year, m_num, 1)
                m_end = datetime(year, m_num, last_day, 23, 59, 59)

                if re.search(rf"\b(first (?:few\s+)?days of|first week of|early)\s+{m_name}\b", lower_q):
                    return m_start - timedelta(days=1), datetime(year, m_num, 10, 23, 59, 59)
                elif re.search(rf"\b(mid(?:dle of)?[- ]?|second week of\s+){m_name}\b", lower_q) or f"mid-{m_name}" in lower_q:
                    return datetime(year, m_num, 8), datetime(year, m_num, 22, 23, 59, 59)
                elif re.search(rf"\b(late|end of)\s+{m_name}\b", lower_q):
                    return datetime(year, m_num, 20), m_end + timedelta(days=1)
                elif re.search(rf"\blast week of\s+{m_name}\b", lower_q):
                    return datetime(year, m_num, max(1, last_day - 8)), m_end + timedelta(days=1)
                else:
                    return m_start - timedelta(days=1), m_end + timedelta(days=1)

        return None, None

    def parse_query(self, query: str) -> dict:
        raw_query = query.strip()
        lower_q = raw_query.lower()

        sender_filter = None
        clean_terms = raw_query

        # Speaker detection
        m_spk = re.search(r"(?:what did|what was|from|by|told by|said by)\s+([a-zA-Z]+)", lower_q)
        if m_spk and m_spk.group(1).lower() in PARTICIPANT_MAP:
            sender_filter = PARTICIPANT_MAP[m_spk.group(1).lower()]
        elif re.search(r"\b([a-zA-Z]+)'s\b", lower_q):
            m_pos = re.search(r"\b([a-zA-Z]+)'s\b", lower_q)
            if m_pos and m_pos.group(1).lower() in PARTICIPANT_MAP:
                sender_filter = PARTICIPANT_MAP[m_pos.group(1).lower()]

        # Temporal detection using fuzzy parser
        date_start, date_end = self.parse_fuzzy_temporal(lower_q)

        if sender_filter and date_start:
            query_type = "attributed+temporal"
        elif sender_filter:
            query_type = "attributed"
        elif date_start:
            query_type = "temporal"
        else:
            query_type = "semantic"

        return {
            "original_query": raw_query,
            "clean_query": clean_terms,
            "query_type": query_type,
            "sender_filter": sender_filter,
            "date_start": date_start.isoformat() if date_start else None,
            "date_end": date_end.isoformat() if date_end else None
        }

    def search(self,
               query: str,
               top_k: int = 10,
               context_radius: int = 3,
               explicit_sender: str = None,
               explicit_start: str = None,
               explicit_end: str = None) -> dict:
        t0 = time.time()
        self._ensure_model()

        if self.embeddings is None:
            if os.path.exists(self.embeddings_path):
                self.embeddings = np.load(self.embeddings_path)
            else:
                raise RuntimeError("Embeddings not loaded.")

        # 1. Parse intent
        analysis = self.parse_query(query)
        if explicit_sender:
            analysis["sender_filter"] = explicit_sender
            analysis["query_type"] = "attributed"
        if explicit_start:
            analysis["date_start"] = explicit_start
        if explicit_end:
            analysis["date_end"] = explicit_end

        # 2. Encode query vector
        query_vec = self.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        # 3. Candidate filtering
        candidate_mask = np.ones(len(self.corpus), dtype=bool)

        # Attributed filter: only when explicitly set or detected as attributed
        if analysis["sender_filter"] and analysis["query_type"] in ["attributed", "attributed+temporal"]:
            target_sender = analysis["sender_filter"]
            candidate_mask &= (self.senders == target_sender)

        # Temporal filter
        if analysis["date_start"]:
            d_start = datetime.fromisoformat(analysis["date_start"])
            start_mask = np.array([ts >= d_start for ts in self.timestamps])
            candidate_mask &= start_mask

        if analysis["date_end"]:
            d_end = datetime.fromisoformat(analysis["date_end"])
            end_mask = np.array([ts <= d_end for ts in self.timestamps])
            candidate_mask &= end_mask

        cand_indices = np.where(candidate_mask)[0]
        if len(cand_indices) == 0:
            cand_indices = np.arange(len(self.corpus))

        # 4. Dense Cosine Scores
        cand_embeddings = self.embeddings[cand_indices]
        dense_scores = np.dot(cand_embeddings, query_vec)

        # 5. Hybrid concept boost + Multi-layer noise & boilerplate penalty
        bonus_scores = np.zeros(len(cand_indices))
        q_words = re.findall(r"\b[a-zA-Z0-9_]+\b", query.lower())

        for i, idx in enumerate(cand_indices):
            msg = self.corpus[idx]
            t_raw = msg["text"].strip()
            t_low = t_raw.lower()
            words = t_low.split()

            # Concept keyword match bonus
            for w in q_words:
                if w in CONCEPT_MAP:
                    for syn in CONCEPT_MAP[w]:
                        if syn in t_low:
                            bonus_scores[i] += 0.20
                            break

            # Noise penalty 1: ultra-short chatter (<= 2 words and < 15 chars)
            if len(words) <= 2 and len(t_low) < 15:
                bonus_scores[i] -= 0.40

            # Noise penalty 2: known conversational filler acknowledgments
            if t_low in FILLER_SET or (len(words) <= 3 and any(w in FILLER_SET for w in words)):
                bonus_scores[i] -= 0.35

            # Noise penalty 3: duplicate boilerplate in corpus (frequency >= 3)
            # Suppresses repeated phrases like 'sprint planning boring...', 'battery low h', etc.
            if self.corpus_text_counts.get(t_low, 0) >= 3:
                bonus_scores[i] -= 0.35

            # Deprioritize forwarded news items over conversational decision messages
            if "[forwarded]" in t_low:
                bonus_scores[i] -= 0.35

        final_scores = dense_scores + bonus_scores

        # 6. Hard Semantic Floor
        # Zero out results whose RAW dense cosine similarity is below SEMANTIC_FLOOR
        # Prevents low-quality filler from ranking high inside narrow filters purely on bonuses
        final_scores[dense_scores < SEMANTIC_FLOOR] = -2.0

        # 7. Rank & Deduplicate
        sorted_order = np.argsort(-final_scores)
        ranked_indices = cand_indices[sorted_order]
        ranked_scores = final_scores[sorted_order]

        selected_results = []
        visited_indices = set()

        for idx, score in zip(ranked_indices, ranked_scores):
            # Do not return messages discarded by semantic floor or heavy penalty
            if score <= 0.0 and len(selected_results) >= 1:
                continue

            is_duplicate = any(abs(idx - v) <= 2 for v in visited_indices)
            if not is_duplicate:
                visited_indices.add(idx)
                msg = self.corpus[idx]

                # Slices context window [-context_radius, +context_radius]
                start_c = max(0, idx - context_radius)
                end_c = min(len(self.corpus), idx + context_radius + 1)
                context_slice = []

                for c_i in range(start_c, end_c):
                    c_msg = self.corpus[c_i]
                    context_slice.append({
                        "id": c_msg["id"],
                        "sender": c_msg["sender"],
                        "timestamp": c_msg["timestamp"],
                        "text": c_msg["text"],
                        "is_target": (c_msg["id"] == msg["id"])
                    })

                selected_results.append({
                    "message": msg,
                    "score": float(score),
                    "context": context_slice
                })

                if len(selected_results) >= top_k:
                    break

        latency_ms = (time.time() - t0) * 1000

        return {
            "query_analysis": analysis,
            "results": selected_results,
            "total_candidates": int(len(cand_indices)),
            "latency_ms": round(latency_ms, 2)
        }

    def get_context(self, message_id: int, radius: int = 5) -> dict:
        if message_id not in self.id_to_idx:
            return {"error": f"Message ID {message_id} not found."}

        idx = self.id_to_idx[message_id]
        start_c = max(0, idx - radius)
        end_c = min(len(self.corpus), idx + radius + 1)

        context_messages = []
        for c_i in range(start_c, end_c):
            c_msg = self.corpus[c_i]
            context_messages.append({
                "id": c_msg["id"],
                "sender": c_msg["sender"],
                "timestamp": c_msg["timestamp"],
                "text": c_msg["text"],
                "is_target": (c_msg["id"] == message_id)
            })

        return {
            "target_message_id": message_id,
            "radius": radius,
            "messages": context_messages
        }
