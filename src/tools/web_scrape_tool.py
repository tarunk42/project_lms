import os
import time
import json
import asyncio
import hashlib
import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse

import requests
import trafilatura
from agents import Agent, Runner, function_tool



def _strip_links(text: str) -> str:
    """Remove URLs/markdown links/citation blobs, keep readable text."""
    # [anchor text](http://url)  -> anchor text
    text = re.sub(r'\[([^\]]+)\]\(\s*(?:https?|ftp)://[^)]+\)', r'\1', text)
    # bare URLs (http/https/www) -> remove
    text = re.sub(r'(?:https?://|www\.)\S+', '', text)
    # Wikipedia-style [[12]] leftovers -> remove
    text = re.sub(r'\[\[\d+\]\]', '', text)
    # Remove citation numbers like [9]
    text = re.sub(r'\[\d+\]', '', text)
    
    # Fix Wikipedia-specific formatting issues with standalone movie/film titles
    # Look for standalone names and film titles with weird formatting
    text = re.sub(r'\n([A-Z][a-zA-Z ]+)(?:\(.*?\))?\n', r' \1 ', text)
    
    # Handle misplaced brackets more aggressively
    text = re.sub(r'\(\s*\)', '', text)  # Empty parentheses
    text = re.sub(r'(?<!\w)\((?!\w)', '', text)  # Opening brackets not followed by word char
    text = re.sub(r'(?<!\w)\)', '', text)  # Closing brackets not preceded by word char
    
    # Fix common patterns in movie descriptions
    text = re.sub(r'\)\s*([A-Z][a-z]+)', r') \1', text) # Fix spacing after closing parentheses
    
    # Fix broken words across lines (no space after period)
    text = re.sub(r'(\w+)\.\n(\w+)', r'\1. \2', text)
    
    # Join lines that appear to be part of the same sentence (more aggressive)
    text = re.sub(r'(\w)\n(\w)', r'\1 \2', text)
    
    # Drop markdown table rows like "| a | b |"
    text = re.sub(r'^\s*\|.*\|\s*$', '', text, flags=re.MULTILINE)
    
    # Fix spacing issues around commas and periods
    text = re.sub(r'\s+,', ',', text)
    text = re.sub(r'\s+\.', '.', text)
    
    # Remove excessive newlines while preserving paragraph structure
    text = re.sub(r'\n{2,}', '\n\n', text)
    
    # Normalize spacing
    text = re.sub(r'[ \t]{2,}', ' ', text)
    
    # Final pass to remove any leftover formatting issues
    text = re.sub(r'\n([a-z])', r' \1', text)  # Join lines starting with lowercase (continuation)
    
    return text.strip()

@function_tool
def scrape_url(
    url: str,
    max_chars: int = 8000,
    with_links: bool = True,
    timeout_s: float = 12.0,
) -> Dict[str, Any]:
    """
    Fetch an HTML page and return main content + metadata for LLM/RAG.

    Args:
      url: Page URL (HTML pages; PDFs not supported here).
      max_chars: Truncate text to reduce tokens/latency (0 = no limit).
      with_links: Include extracted outgoing links (helps citations).
      timeout_s: Network timeout (seconds).

    Returns:
      {
        "url": str,            # original URL
        "final_url": str,      # after redirects
        "title": str|None,
        "author": str|None,
        "date": str|None,      # as provided by page (if any)
        "language": str|None,
        "text": str,           # clean main content (LLM-ready)
        "links": list[dict],   # [{'url','text'}] if available
        "word_count": int,
        "latency_ms": int,
        "sha1": str,           # hash of returned text
        "site": str,           # hostname
        "error": str|None
      }
    """
    t0 = time.time()
    headers = {
        # Polite but effective: some sites block default UA
        "User-Agent": "Mozilla/5.0 (compatible; SimpleScraper/1.0; +https://example.org/agent)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "close",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout_s, allow_redirects=True)
    except requests.RequestException as e:
        return {
            "url": url, "final_url": url, "title": None, "author": None, "date": None,
            "language": None, "text": "", "links": [], "word_count": 0,
            "latency_ms": int((time.time() - t0) * 1000), "sha1": "",
            "site": urlparse(url).hostname or "", "error": f"network_error: {e}"
        }

    ctype = (resp.headers.get("Content-Type") or "").lower()
    if "text/html" not in ctype and "application/xhtml+xml" not in ctype:
        return {
            "url": url, "final_url": resp.url, "title": None, "author": None, "date": None,
            "language": None, "text": "", "links": [], "word_count": 0,
            "latency_ms": int((time.time() - t0) * 1000), "sha1": "",
            "site": urlparse(resp.url).hostname or "", "error": f"unsupported_content_type: {ctype}"
        }

    html = resp.text or ""
    # High-quality main-content extraction (fast, no JS)
    extracted_json = trafilatura.extract(
        html,
        url=resp.url,                          # helps canonicalization
        output_format="json",
        include_links=with_links,
        include_formatting=True,               # preserve headings/code markers
        include_tables=False,                  # disable tables for cleaner text
        favor_precision=True,                  # better precision for docs/news
    )

    if extracted_json:
        data = json.loads(extracted_json)
        title = data.get("title")
        text = data.get("text") or ""
        author = data.get("author")
        date = data.get("date")
        language = data.get("language")
        links = data.get("links") or [] if with_links else []
    else:
        # Fallback: plain text (still robust)
        title = None
        author = None
        date = None
        language = None
        links = []
        text = trafilatura.extract(html, url=resp.url, output_format="txt") or ""
        
    # NEW: strip links from text before truncation/metrics
    text = _strip_links(text)

    if max_chars and len(text) > max_chars:
        text = text[:max_chars].rstrip()

    word_count = len(text.split())
    sha1 = hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()

    return {
        "url": url,
        "final_url": resp.url,
        "title": title,
        "author": author,
        "date": date,
        "language": language,
        "text": text,
        "links": links,
        "word_count": word_count,
        "latency_ms": int((time.time() - t0) * 1000),
        "sha1": sha1,
        "site": urlparse(resp.url).hostname or "",
        "error": None,
    }

# result = scrape_url(
#     url="https://en.wikipedia.org/wiki/Amrita_Rao",
#     max_chars=5000
# )

# for k, v in result.items():
#     print(f"{k}: {v}", "\n")

# scraper_agent = Agent(
#     name="Web Scraper",
#     instructions=(
#         "You extract information from web pages. "
#         "When the user provides a URL (or asks to scrape), CALL the scrape_url tool. "
#         "Then return a elaborate structured summary:\n"
#         "- Title (if any)\n- Site and date\n- 4–6 bullet key points\n- 'Source: <final_url>'\n"
#         "If the page has very little text, say so and include the first 300 characters."
#     ),
#     tools=[scrape_url],
# )

# async def main():
#     user_msg = "Scrape the web page at: 'https://en.wikipedia.org/wiki/Amrita_Rao'."
#     result = await Runner.run(scraper_agent, user_msg)
#     print(result.final_output)

# if __name__ == "__main__":
#     asyncio.run(main())