import os
import requests
from dotenv import load_dotenv

load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY")

def jina_search(query: str, top_k: int = 1):
    """Perform a simple Jina web search via API."""
    url = f"https://s.jina.ai/?q={query}&n={top_k}"
    headers = {
        "Authorization": f"Bearer {JINA_API_KEY}",
        "Accept": "application/json",
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("data", []):
        results.append({
            "title": item.get("title"),
            "url": item.get("url"),
            "description": item.get("description", "")
        })
    return results

if __name__ == "__main__":
    query = "人工智能在医疗领域的应用"
    results = jina_search(query, top_k=3)

    print("搜索结果：")
    for i, r in enumerate(results, 1):
        print(f"{i}. Title: {r['title']}")
        print(f"   URL: {r['url']}")
        print(f"   Description: {r['description']}\n")
