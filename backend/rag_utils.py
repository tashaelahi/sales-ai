# rag_utils.py  – simple cosine‑similarity retriever
import json, os, numpy as np, openai
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- load embeddings & pages once ------------------------------------------------
EMB = np.load("sunset_embeds.npy")              # shape (N, 1536)
with open("sunset_pages.json") as f:
    PAGE_DICT = json.load(f)                    # {url: chunk_text}
URLS  = list(PAGE_DICT.keys())
CHUNK = list(PAGE_DICT.values())

def _embed(text: str) -> np.ndarray:
    out = openai.Embedding.create(
        input=[text],
        model="text-embedding-ada-002"
    )
    return np.array(out["data"][0]["embedding"], dtype=np.float32)

def retrieve_relevant_snippets(query: str, top_k: int = 3):
    q = _embed(query)
    sims = (EMB @ q) / (np.linalg.norm(EMB, axis=1) * np.linalg.norm(q))
    idxs = sims.argsort()[-top_k:][::-1]
    snippets = [CHUNK[i] for i in idxs]
    urls     = [URLS[i]  for i in idxs]
    return snippets, urls
