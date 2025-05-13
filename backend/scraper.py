import requests
import time
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from supabase import create_client
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase_client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

JINA_HEADERS = {
    "Authorization": "Bearer jina_8ef91cd238f645908f28af84c70f42d726QtQYOZ7gEycuaU7PPMfcdZzG78"
}

def fetch_jina(url, retries=5, delay=5, return_format="text"):
    headers = JINA_HEADERS.copy()
    if return_format == "html":
        headers["X-Return-Format"] = "html"

    full_url = f"https://r.jina.ai/{url}"

    for attempt in range(retries):
        response = requests.get(full_url, headers=headers)
        if response.status_code == 200:
            return response.text
        print(f"Attempt {attempt + 1} failed. Retrying in {delay} seconds...")
        time.sleep(delay)

    raise Exception(f"Failed to retrieve content after {retries} attempts.")

def extract_content(url):
    return fetch_jina(url, return_format="text")

def split_into_chunks(text, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_text(text)

def clean_chunk(chunk):
    lines = chunk.splitlines()
    stripped_lines = [line.strip() for line in lines if line.strip()]
    return '\n'.join(stripped_lines)

def embed_chunk(chunk, model="text-embedding-3-small"):
    response = openai_client.embeddings.create(input=chunk, model=model)
    return response.data[0].embedding

def insert_chunk(url, chunk, embedding):
    data = {
        "url": url,
        "content": chunk,
        "embedding": embedding
    }
    supabase_client.table("partselect_chunks").insert(data).execute()

def process_and_store_url(url):
    try:
        print(f"\nProcessing: {url}")
        raw_text = fetch_jina(url, return_format="text")
        chunks = split_into_chunks(raw_text)
        
        for i, chunk in enumerate(chunks, start=1):
            cleaned = clean_chunk(chunk)
            if cleaned:
                try:
                    embedding = embed_chunk(cleaned)
                    insert_chunk(url, cleaned, embedding)
                except Exception as e:
                    print(f"Failed to embed/insert chunk {i} of {len(chunks)} for {url}: {e}")
        
        print(f"Done storing chunks for {url}")
    
    except Exception as e:
        print(f"Failed to process {url}: {e}")

def get_links_from_page(url):
    html = fetch_jina(url, return_format="html")
    soup = BeautifulSoup(html, "html.parser")
    return [urljoin(url, a['href']) for a in soup.find_all('a', href=True) if "SourceCode" in a['href']]

def crawl_links(start_url, max_depth):
    visited = set()
    results = set()

    def recurse(url, depth):
        if depth > max_depth or url in visited:
            return
        visited.add(url)
        print(f"Visiting: {url}")
        links = get_links_from_page(url)
        for link in links:
            if link not in visited:
                results.add(link)
                recurse(link, depth + 1)

    recurse(start_url, 0)
    return list(results)

def main():
    seed_urls = [
        "https://www.partselect.com/Dishwasher-Parts.htm",
        "https://www.partselect.com/Refrigerator-Parts.htm"
    ]

    all_links = set()
    for url in seed_urls:
        links = crawl_links(url, max_depth=0)
        all_links.update(links)

    print(f"\nDiscovered {len(all_links)} unique links.\n")

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(tqdm(executor.map(process_and_store_url, all_links), total=len(all_links)))

if __name__ == "__main__":
    main()
