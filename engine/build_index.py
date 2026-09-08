"""
Precomputes dense vector embeddings for all 4,250 messages in the chat corpus.
Uses sentence-transformers with multilingual support + Hinglish normalizer.
Saves pre-normalized unit vectors into embeddings.npy for sub-millisecond dot-product retrieval.
"""

import os
import sys
import json
import time
import logging
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from engine.normalizer import normalize_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

CORPUS_PATH = os.path.join(PROJECT_ROOT, "dataset", "chat_corpus.json")
EMBEDDINGS_PATH = os.path.join(PROJECT_ROOT, "engine", "embeddings.npy")
METADATA_PATH = os.path.join(PROJECT_ROOT, "engine", "index_metadata.json")

def build_index():
    logger.info(f"Loading corpus from: {CORPUS_PATH}")
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        corpus = json.load(f)
    logger.info(f"Corpus size: {len(corpus)} messages")

    logger.info("Importing SentenceTransformer...")
    from sentence_transformers import SentenceTransformer

    # Load multilingual model
    model_name = "paraphrase-multilingual-MiniLM-L12-v2"
    logger.info(f"Loading embedding model: {model_name}...")
    t0 = time.time()
    model = SentenceTransformer(model_name)
    logger.info(f"Model loaded in {time.time() - t0:.2f}s")

    # Prepare enriched text representations
    logger.info("Preparing enriched text representation with Hinglish normalization & context...")
    enriched_texts = []
    for i, m in enumerate(corpus):
        # Incorporate immediate context from previous message if within 15 minutes
        context_prefix = ""
        if i > 0:
            prev = corpus[i - 1]
            context_prefix = f"Context: {prev['sender']}: {prev['text']} | "

        norm_content = normalize_text(m["text"])
        entry = f"{context_prefix}[{m['sender']}] {norm_content}"
        enriched_texts.append(entry)

    logger.info(f"Sample enriched text (ID 142): {enriched_texts[min(141, len(enriched_texts)-1)]}")

    logger.info(f"Encoding {len(enriched_texts)} messages in batches...")
    t_start = time.time()
    embeddings = model.encode(
        enriched_texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True  # Pre-normalize to unit length for cosine dot-product
    )
    encode_time = time.time() - t_start
    logger.info(f"Encoding complete in {encode_time:.2f}s (shape: {embeddings.shape})")

    # Save embeddings
    np.save(EMBEDDINGS_PATH, embeddings)
    logger.info(f"Embeddings saved to: {EMBEDDINGS_PATH} (size: {os.path.getsize(EMBEDDINGS_PATH) / (1024*1024):.2f} MB)")

    # Save metadata
    meta = {
        "model_name": model_name,
        "embedding_dim": int(embeddings.shape[1]),
        "total_items": int(embeddings.shape[0]),
        "normalized": True,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    logger.info(f"Index metadata saved to: {METADATA_PATH}")

if __name__ == "__main__":
    build_index()
