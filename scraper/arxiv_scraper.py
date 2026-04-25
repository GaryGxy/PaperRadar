"""
arXiv Scraper - 抓取arXiv论文元数据（带重试+延时）
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict
import time
import random


ARXIV_API = "http://export.arxiv.org/api/query"

# 重试次数
MAX_RETRIES = 3
RETRY_DELAY_BASE = 5  # 秒


def build_query(keywords: List[str], days_back: int = 7, max_results: int = 50) -> str:
    """构建arXiv搜索查询"""
    keyword_str = " OR ".join(f'"{kw}"' for kw in keywords)
    date_cutoff = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    query = f'({keyword_str}) AND submittedDate:[{date_cutoff} TO NOW]'
    return query


def fetch_papers(keywords: List[str], days_back: int = 7, max_results: int = 50) -> List[Dict]:
    """从arXiv抓取论文（带重试+延时）"""
    query = build_query(keywords, days_back, max_results)
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    
    for attempt in range(MAX_RETRIES):
        try:
            # 延时（随机 jitter）
            if attempt > 0:
                delay = RETRY_DELAY_BASE * (2 ** attempt) + random.uniform(1, 3)
                print(f"[arXiv] 重试 #{attempt+1}，等待 {delay:.1f}s...")
                time.sleep(delay)
            
            req = urllib.request.Request(url, headers={"User-Agent": "PaperRadar/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                xml_text = response.read().decode("utf-8")
            
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = int(e.headers.get("Retry-After", RETRY_DELAY_BASE * (2 ** attempt)))
                print(f"[arXiv] 限流 (429)，等待 {wait}s...")
                time.sleep(wait)
                continue
            print(f"[arXiv] HTTP错误: {e.code} {e.reason}")
            if attempt == MAX_RETRIES - 1:
                return []
        except Exception as e:
            print(f"[arXiv] 请求失败 [{attempt+1}/{MAX_RETRIES}]: {e}")
            if attempt == MAX_RETRIES - 1:
                return []
            time.sleep(RETRY_DELAY_BASE)
            continue
        
        # 解析 XML
        root = ET.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        
        papers = []
        for entry in root.findall("atom:entry", ns):
            paper = {
                "id": "",
                "title": "",
                "summary": "",
                "authors": [],
                "published": "",
                "updated": "",
                "categories": [],
                "pdf_url": "",
                "source": "arXiv",
                "citations": 0,
            }
            
            def get_text(tag):
                found = entry.find(f"{{{ns['atom']}}}{tag}")
                return found.text or "" if found is not None else ""
            
            paper["id"] = get_text("id")
            paper["title"] = get_text("title").replace("\n", " ").strip()
            paper["summary"] = get_text("summary").replace("\n", " ").strip()
            paper["published"] = get_text("published")
            paper["updated"] = get_text("updated")
            
            paper["authors"] = [
                a.find(f"{{{ns['atom']}}}name").text or ""
                for a in entry.findall(f"{{{ns['atom']}}}author")
                if a.find(f"{{{ns['atom']}}}name") is not None
            ]
            
            paper["categories"] = [
                c.get("term", "")
                for c in entry.findall(f"{{{ns['atom']}}}category")
            ]
            
            # PDF link
            for link in entry.findall(f"{{{ns['atom']}}}link"):
                if link.get("title") == "pdf":
                    paper["pdf_url"] = link.get("href", "")
                    break
            
            papers.append(paper)
        
        print(f"[arXiv] 抓取到 {len(papers)} 篇论文")
        return papers
    
    return []


if __name__ == "__main__":
    test_keywords = ["large language model", "LLM"]
    papers = fetch_papers(test_keywords, days_back=7, max_results=5)
    for p in papers:
        print(f"  - {p['title'][:60]}...")
