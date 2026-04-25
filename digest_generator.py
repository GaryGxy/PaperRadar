"""
Digest Generator - 生成每日论文摘要digest
"""

import os
from datetime import datetime
from typing import List, Dict


def generate_digest(
    papers: List[Dict],
    topic: str = "",
    output_path: str = "./output/digest/YYYY-MM-DD.md",
) -> str:
    """
    生成每日digest Markdown文件
    
    每篇论文包含:
    - 标题 + 链接
    - 引用量
    - 一句话描述（summary或LLM生成）
    """
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = output_path.replace("YYYY-MM-DD", today)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 按topic分组
    by_topic = {}
    for p in papers:
        t = p.get("topic", "general")
        by_topic.setdefault(t, []).append(p)
    
    lines = [
        f"# 📚 PaperRadar 每日论文速递 — {today}",
        "",
        f"**生成时间:** {datetime.now().strftime('%H:%M:%S')}",
        f"**论文总数:** {len(papers)} 篇",
        "",
        "---",
    ]
    
    for topic_name, topic_papers in by_topic.items():
        lines.append(f"\n## 🔬 {topic_name} ({len(topic_papers)} 篇)\n")
        
        for i, p in enumerate(topic_papers, 1):
            title = p.get("title", "Untitled")
            link = p.get("link", "")
            citations = p.get("citations", 0)
            summary = p.get("_generated_summary", "") or _truncate(p.get("summary", ""), 150)
            authors = ", ".join(p.get("authors", [])[:3])
            if len(p.get("authors", [])) > 3:
                authors += " et al."
            
            lines.append(f"### {i}. {title}")
            lines.append("")
            lines.append(f"**👥 作者:** {authors}")
            lines.append(f"**📅 发表:** {p.get('published', '')[:10]}  |  **📖 引用:** {citations}")
            lines.append(f"**🔗 [原文链接]({link})**")
            if p.get("pdf_url"):
                lines.append(f"**📄 [PDF下载]({p.get('pdf_url', '')})**")
            lines.append("")
            if summary:
                lines.append(f"> {summary}")
            lines.append("")
    
    content = "\n".join(lines)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"[Digest] 生成完毕 → {output_path}")
    return output_path


def generate_simple_digest(papers: List[Dict]) -> str:
    """
    生成纯文本简洁版digest（供其他工具调用）
    """
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"PaperRadar 每日速递 {today}\n{'='*40}\n"]
    
    by_topic = {}
    for p in papers:
        t = p.get("topic", "general")
        by_topic.setdefault(t, []).append(p)
    
    for topic_name, topic_papers in by_topic.items():
        lines.append(f"\n## {topic_name} ({len(topic_papers)}篇)\n")
        for i, p in enumerate(topic_papers, 1):
            lines.append(f"{i}. {p.get('title', 'Untitled')}")
            lines.append(f"   引用:{p.get('citations', 0)} | {p.get('link', '')}")
            if p.get("_generated_summary"):
                lines.append(f"   → {p['_generated_summary'][:100]}")
            lines.append("")
    
    return "\n".join(lines)


def _truncate(text: str, max_len: int = 150) -> str:
    """截断文本"""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


if __name__ == "__main__":
    test_papers = [
        {
            "title": "Scaling Law for Neural Language Models",
            "authors": ["Jared Kaplan", "Sam McCandlish"],
            "published": "2026-04-20",
            "citations": 2300,
            "link": "https://arxiv.org/abs/2001.08361",
            "topic": "LLM",
            "summary": "这篇论文研究了语言模型的扩展法则，发现模型规模、数据集大小和计算量之间的幂律关系。",
        },
        {
            "title": "Robot Learning with Foundation Models",
            "authors": ["Chen Wang"],
            "published": "2026-04-22",
            "citations": 450,
            "link": "https://arxiv.org/abs/2604.01234",
            "topic": "Robotics",
            "summary": "研究如何利用基础模型提升机器人操控能力。",
        },
    ]
    
    path = generate_digest(test_papers)
    print(f"生成于: {path}")
