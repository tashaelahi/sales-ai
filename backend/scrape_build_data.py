"""
scrape_build_data.py
Run once to scrape https://www.sunset17.com/, extract readable text,
chunk into paragraphs (~200-400 chars), embed each chunk with OpenAI,
and save sunset_pages.json, sunset_urls.json, sunset_embeds.npy.
"""
import os, re, json, time, numpy as np, requests, openai
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
from dotenv import load_dotenv
load_dotenv()

ROOT = "https://www.sunset17.com/"

openai.api_key = os.getenv("OPENAI_API_KEY")
HEADERS = {"User-Agent": "Sunset17-scraper/1.0"}

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def get_links(html, base):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base, a["href"])
        if href.startswith(ROOT):
            parsed = urlparse(href)
            href = parsed.scheme + "://" + parsed.netloc + parsed.path  # strip params/query
            links.add(href)
    return links

def scrape_site():
    to_visit = {ROOT}
    visited  = set()
    pages    = {}

    while to_visit:
        url = to_visit.pop()
        if url in visited:
            continue
        try:
            html = requests.get(url, headers=HEADERS, timeout=15).text
        except Exception as e:
            print("fail", url, e)
            continue

        visited.add(url)
        soup = BeautifulSoup(html, "html.parser")
        # remove nav/footer
        for tag in soup(["nav", "footer", "script", "style"]):
            tag.decompose()
        text = clean_text(soup.get_text(" "))

        pages[url] = text
        to_visit.update(get_links(html, url))

    return pages

def embed_chunks(pages):
    urls, chunks, embeds = [], [], []
    for url, text in pages.items():
        # chunk by paragraphs
        parts = [clean_text(p) for p in text.split("\n") if len(clean_text(p)) > 80]
        for part in parts:
            urls.append(url)
            chunks.append(part)
    # batch embed
    for i in tqdm(range(0, len(chunks), 96), desc="embedding"):
        batch = chunks[i:i+96]
        resp = openai.embeddings.create(
            input=batch,
            model="text-embedding-ada-002"
        )
        embeds.extend([np.array(d.embedding, dtype=np.float32) for d in resp.data])
        time.sleep(0.5)  # mind rate limit
    return urls, chunks, np.vstack(embeds)

if __name__ == "__main__":
    print("Scraping website ...")
    pages = scrape_site()
    print(f"Collected {len(pages)} pages.")

    print("Embedding chunks ...")
    urls, chunks, embs = embed_chunks(pages)

    with open("sunset_pages.json", "w") as f:
        json.dump({u: c for u, c in zip(urls, chunks)}, f)

    with open("sunset_urls.json", "w") as f:
        json.dump(urls, f)

    np.save("sunset_embeds.npy", embs)
    print("Saved sunset_pages.json, sunset_urls.json, sunset_embeds.npy")
