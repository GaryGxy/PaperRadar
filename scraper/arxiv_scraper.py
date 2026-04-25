"""
arXiv Scraper - 抓取arXiv论文元数据
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict
import time


ARXIV_API = "http://export.arxiv.org/api/query"


def build_query(keywords: List[str], days_back: int = 7, max_results: int = 50) -> str:
    """构建arXiv搜索查询"""
    keyword_str = " OR ".join(f'"{kw}"' for kw in keywords)
    date_cutoff = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    query = f'({keyword_str}) AND submittedDate:[{date_cutoff} TO NOW]'
    return query


def parse_arxiv_entry(entry: Dict) -> Dict:
    """解析单条arXiv论文记录"""
    def get_text(elem, tag):
        found = elem.find(f"./{{{elem.attrib.get('xmlns', '')}}}{tag}")
        return found.text if found is not None else ""

    authors = [a.get("name", "") for a in entry.get("authors", [])]
    
    return {
        "id": entry.get("id", ""),
        "title": entry.get("title", "").replace("\n", " ").strip(),
        "summary": entry.get("summary", "").replace("\n", " ").strip(),
        "authors": authors,
        "published": entry.get("published", ""),
        "updated": entry.get("updated", ""),
        "categories": entry.get("categories", []),
        "pdf_url": entry.get("pdf_url", ""),
        "link": entry.get("id", ""),
        "source": "arXiv",
        "citations": 0,  # arXiv不提供引用数
    }


def fetch_papers(keywords: List[str], days_back: int = 7, max_results: int = 50) -> List[Dict]:
    """从arXiv抓取论文"""
    query = build_query(keywords, days_back, max_results)
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            xml_text = response.read().decode("utf-8")
    except Exception as e:
        print(f"[arXiv] 请求失败: {e}")
        return []
    
    root = ET.fromstring(xml_text)
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    
    papers = []
    for entry in root.findall("atom:entry", ns):
        paper = {
            "id": (entry.find("atom:id", ns) or entry.find("id")).text or "",
            "title": (entry.find("atom:title", ns) or entry.find("title")).text or "",
            "summary": (entry.find("atom:summary", ns) or entry.find("summary")).text or "",
            "published": (entry.find("atom:published", ns) or entry.find("published")).text or "",
            "updated": (entry.find("atom:updated", ns) or entry.find("updated")).text or "",
            "authors": [a.get("name", "") for a in entry.findall("atom:author", ns)],
            "categories": [c.get("term", "") for c in entry.findall("atom:category", ns)],
            "pdf_url": "",
            "source": "arXiv",
            "citations": 0,
        }
        
        # 获取PDF链接
        for link in entry.findall("atom:link", ns):
            if link.get("title") == "pdf":
                paper["pdf_url"] = link.get("href", "")
                break
        
        paper["title"] = paper["title"].replace("\n", " ").strip()
        paper["summary"] = paper["summary"].replace("\n", " ").strip()
        
        papers.append(paper)
    
    print(f"[arXiv] 抓取到 {len(papers)} 篇论文")
    return papers


if __name__ == "__main__":
    # 简单测试
    test_keywords = ["large language model", "LLM", "GPT"]
    papers = fetch_papers(test_keywords, days_back=7, max_results=5)
    for p in papers:
        print(f"  - {p['title'][:60]}...")
