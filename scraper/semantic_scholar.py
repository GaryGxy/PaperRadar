"""
Semantic Scholar Scraper - 通过Semantic Scholar API抓取论文
API文档: https://api.semanticscholar.org/
"""

import requests
import time
from typing import List, Dict, Optional

SS_API_KEY = ""  # 可选，用户可填入自己的API Key
SS_BASE = "https://api.semanticscholar.org/graph/v1"


def fetch_papers_by_keywords(
    keywords: List[str],
    year: Optional[int] = None,
    max_results: int = 50,
    api_key: str = ""
) -> List[Dict]:
    """通过关键词搜索 Semantic Scholar"""
    query = " OR ".join(f'"{kw}"' for kw in keywords)
    
    headers = {"x-api-key": api_key} if api_key else {}
    
    # 先搜索论文ID列表
    search_url = f"{SS_BASE}/paper/search"
    params = {
        "query": query,
        "year": year,
        "limit": min(max_results, 100),
        "fields": "title,abstract,authors,year,publicationDate,citationCount,openAccessPdf,url,externalIds",
    }
    
    try:
        resp = requests.get(search_url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[Semantic Scholar] 搜索失败: {e}")
        return []
    
    papers = []
    for item in data.get("data", []):
        paper = {
            "id": item.get("externalIds", {}).get("ArXiv", "") or item.get("paperId", ""),
            "title": item.get("title", ""),
            "summary": item.get("abstract", "") or "",
            "authors": [a.get("name", "") for a in item.get("authors", [])],
            "published": item.get("publicationDate", ""),
            "year": item.get("year", ""),
            "categories": [],
            "pdf_url": (item.get("openAccessPdf") or {}).get("url", "") if item.get("openAccessPdf") else "",
            "link": item.get("url", ""),
            "source": "Semantic Scholar",
            "citations": item.get("citationCount", 0) or 0,
        }
        papers.append(paper)
    
    print(f"[Semantic Scholar] 搜索到 {len(papers)} 篇论文")
    return papers


def fetch_paper_details(paper_id: str, api_key: str = "") -> Optional[Dict]:
    """获取单篇论文详细信息"""
    headers = {"x-api-key": api_key} if api_key else {}
    url = f"{SS_BASE}/paper/{paper_id}"
    params = {
        "fields": "title,abstract,authors,year,publicationDate,citationCount,openAccessPdf,url,externalIds,venue"
    }
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        item = resp.json()
        
        return {
            "id": item.get("externalIds", {}).get("ArXiv", "") or item.get("paperId", ""),
            "title": item.get("title", ""),
            "summary": item.get("abstract", "") or "",
            "authors": [a.get("name", "") for a in item.get("authors", [])],
            "published": item.get("publicationDate", ""),
            "year": item.get("year", ""),
            "venue": item.get("venue", ""),
            "pdf_url": (item.get("openAccessPdf") or {}).get("url", "") if item.get("openAccessPdf") else "",
            "link": item.get("url", ""),
            "source": "Semantic Scholar",
            "citations": item.get("citationCount", 0) or 0,
        }
    except Exception as e:
        print(f"[Semantic Scholar] 获取详情失败 ({paper_id}): {e}")
        return None


if __name__ == "__main__":
    test_keywords = ["large language model", "RLHF"]
    papers = fetch_papers_by_keywords(test_keywords, year=2026, max_results=5)
    for p in papers:
        print(f"  - {p['title'][:60]}... (cited: {p['citations']})")
