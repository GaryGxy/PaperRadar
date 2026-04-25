"""
Archiver - 将论文归档为 Markdown 文件 + 统一索引
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict


def slugify(text: str) -> str:
    """将标题转换为安全的文件名slug"""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[_\s]+", "-", text)
    return text[:80]


def paper_to_markdown(paper: Dict, summary: str = "") -> str:
    """将论文转换为带 YAML frontmatter 的 Markdown"""
    
    # 构建 frontmatter
    lines = [
        "---",
        f"title: \"{_escape_yaml(paper.get('title', ''))}\"",
        f"authors: [{', '.join(_escape_yaml(a) for a in paper.get('authors', []))}]",
        f"published: \"{paper.get('published', '')}\"",
        f"year: {paper.get('year', '')}",
        f"source: \"{paper.get('source', '')}\"",
        f"citations: {paper.get('citations', 0)}",
        f"categories: [{', '.join(paper.get('categories', []))}]",
        f"link: \"{paper.get('link', '')}\"",
        f"pdf_url: \"{paper.get('pdf_url', '')}\"",
        f"topic: \"{paper.get('topic', '')}\"",
        f"archived_at: \"{datetime.now().isoformat()}\"",
        f"_score: {paper.get('_score', 0)}",
        "---",
        "",
        f"# {paper.get('title', '')}",
        "",
        f"**作者:** {', '.join(paper.get('authors', [])[:5])}{' et al.' if len(paper.get('authors', [])) > 5 else ''}",
        "",
        f"**发表:** {paper.get('published', '')}  |  **来源:** {paper.get('source', '')}  |  **引用:** {paper.get('citations', 0)}",
        "",
        f"**原文链接:** [{paper.get('link', '')}]({paper.get('link', '')})",
    ]
    
    if paper.get("pdf_url"):
        lines.append(f"**PDF:** [下载]({paper['pdf_url']})")
    
    lines.append("")
    
    if summary:
        lines.append("## 摘要总结")
        lines.append("")
        lines.append(summary)
        lines.append("")
    
    if paper.get("summary"):
        lines.append("## 原文摘要")
        lines.append("")
        lines.append(paper["summary"][:2000])  # 防止太长
        lines.append("")
    
    return "\n".join(lines)


def _escape_yaml(text: str) -> str:
    """简单转义YAML特殊字符"""
    if not text:
        return ""
    text = text.replace('"', '\\"').replace("\n", " ")
    return text.strip()


def archive_papers(
    papers: List[Dict],
    output_dir: str = "./output/archives",
    create_summary: bool = False,
) -> List[str]:
    """
    将论文列表归档到指定目录
    
    返回: 归档的文件路径列表
    """
    os.makedirs(output_dir, exist_ok=True)
    archived_files = []
    
    for paper in papers:
        topic = paper.get("topic", "general").replace(" ", "_").lower()
        topic_dir = os.path.join(output_dir, topic)
        os.makedirs(topic_dir, exist_ok=True)
        
        # 生成文件名
        pub_date = paper.get("published", "unknown")[:10]
        slug = slugify(paper.get("title", "untitled"))[:60]
        filename = f"{pub_date}_{slug}.md"
        filepath = os.path.join(topic_dir, filename)
        
        # 避免文件名冲突
        counter = 1
        base_filepath = filepath
        while os.path.exists(filepath):
            filepath = base_filepath.replace(".md", f"_{counter}.md")
            counter += 1
        
        # 生成summary（预留，后续可接入LLM）
        summary = paper.get("_generated_summary", "")
        
        content = paper_to_markdown(paper, summary)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        archived_files.append(filepath)
        paper["_archived_path"] = filepath
    
    return archived_files


def build_index(papers: List[Dict], output_path: str = "./output/knowledge_base.json") -> str:
    """
    构建统一索引文件（供RAG/AI工具使用）
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    index = {
        "generated_at": datetime.now().isoformat(),
        "total_papers": len(papers),
        "papers": [
            {
                "title": p.get("title", ""),
                "authors": p.get("authors", []),
                "published": p.get("published", ""),
                "year": p.get("year", ""),
                "source": p.get("source", ""),
                "citations": p.get("citations", 0),
                "topic": p.get("topic", ""),
                "link": p.get("link", ""),
                "pdf_url": p.get("pdf_url", ""),
                "score": p.get("_score", 0),
                "summary": p.get("_generated_summary", ""),
                "archived_path": p.get("_archived_path", ""),
            }
            for p in papers
        ],
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    return output_path


if __name__ == "__main__":
    test_paper = {
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "published": "2017-06-12",
        "year": 2017,
        "source": "arXiv",
        "citations": 98000,
        "categories": ["cs.CL", "cs.LG"],
        "link": "https://arxiv.org/abs/1706.03762",
        "pdf_url": "https://arxiv.org/pdf/1706.03762",
        "topic": "LLM",
        "_score": 0.95,
    }
    
    md = paper_to_markdown(test_paper, "这是一篇关于Transformer的论文...")
    print(md[:500])
