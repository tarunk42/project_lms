import os, requests
from urllib.parse import urlparse
from typing import List, Dict, Optional
from agents import function_tool, Agent, Runner
from dotenv import load_dotenv
import asyncio

load_dotenv()  # Load environment variables from .env file

BRAVE_WEB_URL = "https://api.search.brave.com/res/v1/web/search"

api_key = os.getenv("BRAVE_SEARCH_API_KEY")
if not api_key:
    raise RuntimeError("Missing BRAVE_SEARCH_API_KEY in environment.")


def _norm_domain(d: str) -> str:
    d = d.strip().lower()
    if d.startswith(("http://", "https://")):
        d = urlparse(d).netloc
    return d.lstrip(".")

# Default list of domains to exclude from search results
DEFAULT_EXCLUDE_DOMAINS = [
    "pinterest.com",
    "facebook.com", 
    "instagram.com", 
    "tiktok.com",
]

@function_tool
def brave_web_search(
    q: str,
    count: int = 5,
    country: str = "us",
    search_lang: str = "en",
    freshness: Optional[str] = None,  # e.g. "pd", "pw", "pm", "py" or "YYYY-MM-DDtoYYYY-MM-DD",
    exclude_domains: Optional[List[str]] = DEFAULT_EXCLUDE_DOMAINS,   
    goggles_urls: Optional[List[str]] = None,      
) -> List[Dict[str, str]]:
    """
    Search the web via Brave and return top results (title, url, snippet).

    Params mirror Brave docs:
      - q (required): search query.
      - count (<=20): number of web results.
      - country (2-letter), search_lang, freshness (optional window).
    """

    ex = []
    for raw in exclude_domains or []:
        d = _norm_domain(raw)
        if not d or "/" in d:  # keep it conservative
            continue
        ex += [f"NOT site:{d}", f"NOT site:*.{d}"]  # root + subdomains

    q_final = " ".join(([q] + ex))

    params = {
        "q": q_final,  # Use the query with exclusions
        "count": max(1, min(count, 20)),     # Brave caps web count at 20
        "country": country,
        "search_lang": search_lang,
        "result_filter": "web",               # only web results
        "text_decorations": "false",          # plain snippets
    }
    if freshness:
        params["freshness"] = freshness
    
    if goggles_urls:
        params["goggles"] = goggles_urls  # requests will repeat the key

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,      # required auth header
    }

    resp = requests.get(BRAVE_WEB_URL, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # Brave returns web results under data["web"]["results"] with title/url/description
    out: List[Dict[str, str]] = []
    for item in (data.get("web", {}) or {}).get("results", []) or []:
        out.append({
            "title": item.get("title", "")[:300],
            "url": item.get("url", ""),
            "snippet": item.get("description", "")[:500],
        })
        if len(out) >= params["count"]:
            break

    return out or [{"title": "No results", "url": "", "snippet": ""}]


# results = brave_web_search(
#         q="Amitabh Bachchan",
#         count=5, country="in", search_lang="en"
#     )

# for r in results:
#     print(f"- {r['title']} ({r['url']})\n  {r['snippet']}\n")

# search_agent = Agent(
#     name="Brave Searcher",
#     instructions=(
#         "You search the web. When the user asks to look something up, "
#         "CALL the brave_web_search tool. Then return a concise bullet list:\n"
#         "- Title — URL\n  One-line takeaway."
#     ),
#     model="gpt-4o-mini",
#     tools=[brave_web_search],
# )

# async def main():
#     user_msg = "Search the web for: 'python virtualenv tutorial' (top 5)."
#     result = await Runner.run(search_agent, user_msg)
#     print(result.final_output)

# if __name__ == "__main__":
#     asyncio.run(main())