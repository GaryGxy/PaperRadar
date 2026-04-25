"""
Ranking算法 - 基于时间衰减 + 引用量权重排序
"""

import math
from datetime import datetime
from typing import List, Dict


def time_decay_score(published_str: str, half_life_days: int = 7) -> float:
    """计算时间衰减分数 (指数衰减)"""
    try:
        published = datetime.fromisoformat(published_str.replace("Z", "+00:00").split("T")[0])
        now = datetime.now()
        days_ago = (now - published).days
        if days_ago < 0:
            days_ago = 0
        # 指数衰减: score = 0.5^(days/half_life)
        return math.pow(0.5, days_ago / half_life_days)
    except:
        return 0.0


def normalize_citations(citations: int, max_citations: float = 100.0) -> float:
    """归一化引用量分数"""
    if max_citations <= 0:
        return 0.0
    return min(citations / max_citations, 1.0)


def rank_papers(
    papers: List[Dict],
    time_decay_days: int = 7,
    citation_weight: float = 0.6,
    recency_weight: float = 0.4,
    min_citations: int = 0,
) -> List[Dict]:
    """
    对论文列表进行综合排序
    
    公式: score = citation_weight * norm_citations + recency_weight * time_decay
    """
    if not papers:
        return []
    
    # 过滤最低引用量
    filtered = [p for p in papers if p.get("citations", 0) >= min_citations]
    
    # 计算最大引用量用于归一化
    max_cites = max((p.get("citations", 0) for p in filtered), default=1)
    
    scored = []
    for p in filtered:
        cite_score = normalize_citations(p.get("citations", 0), max_cites)
        time_score = time_decay_score(p.get("published", ""), time_decay_days)
        
        final_score = citation_weight * cite_score + recency_weight * time_score
        
        scored.append((final_score, -_parse_date(p.get("published", "")), p))
    
    # 按分数降序，同分按日期降序
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    
    ranked = []
    for score, _, paper in scored:
        paper["_score"] = round(score, 4)
        ranked.append(paper)
    
    return ranked


def _parse_date(date_str: str) -> datetime:
    """解析日期字符串"""
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00").split("T")[0])
    except:
        return datetime.min


if __name__ == "__main__":
    # 测试
    test_papers = [
        {"title": "GPT-4", "citations": 5000, "published": "2026-04-20"},
        {"title": "New LLM", "citations": 10, "published": "2026-04-24"},
        {"title": "Old paper", "citations": 100, "published": "2026-03-01"},
    ]
    ranked = rank_papers(test_papers)
    for p in ranked:
        print(f"[{p['_score']}] {p['title']} (cited: {p['citations']})")
