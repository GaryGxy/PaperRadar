"""
PaperRadar 主入口
用法: python main.py [--config CONFIG_PATH] [--topics TOPIC1,TOPIC2] [--days DAYS]
"""

import argparse
import os
import sys
import yaml
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper.arxiv_scraper import fetch_papers as fetch_arxiv
from scraper.semantic_scholar import fetch_papers_by_keywords
from ranker import rank_papers
from archiver import archive_papers, build_index
from digest_generator import generate_digest, generate_simple_digest


def load_config(config_path: str = "./config.yaml") -> dict:
    """加载配置文件"""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_pipeline(
    config: dict,
    topics: list = None,
    days_back: int = None,
    api_key: str = "",
    verbose: bool = True,
) -> list:
    """
    运行完整Pipeline: 抓取 → 排序 → 归档 → 生成digest
    返回: 所有归档的论文列表
    """
    
    # 读取配置
    tracking_topics = config.get("tracking_topics", [])
    archive_config = config.get("archive", {})
    ranking_config = config.get("ranking", {})
    
    if days_back is None:
        days_back = archive_config.get("paper_age_days", 7)
    
    max_papers = archive_config.get("max_papers_per_topic", 20)
    output_dir = archive_config.get("output_dir", "./output/archives")
    digest_dir = archive_config.get("digest_dir", "./output/digest")
    
    if topics:
        # 只跑指定的topics
        tracking_topics = [t for t in tracking_topics if t.get("name") in topics and t.get("enabled", True)]
    
    all_papers = []
    
    if verbose:
        print("=" * 50)
        print("PaperRadar 启动")
        print(f"追踪领域: {[t['name'] for t in tracking_topics]}")
        print(f"时间范围: 近{days_back}天")
        print("=" * 50)
    
    for topic_cfg in tracking_topics:
        if not topic_cfg.get("enabled", True):
            continue
        
        topic_name = topic_cfg["name"]
        keywords = topic_cfg.get("keywords", [])
        
        if not keywords:
            print(f"[{topic_name}] 无关键词配置，跳过")
            continue
        
        if verbose:
            print(f"\n📡 抓取领域: {topic_name}")
        
        # 1. 抓取 arXiv
        arxiv_papers = fetch_arxiv(keywords, days_back=days_back, max_results=max_papers * 2)
        for p in arxiv_papers:
            p["topic"] = topic_name
        
        # 2. 抓取 Semantic Scholar（如果有API Key）
        ss_papers = []
        if api_key or True:  # 无API Key也能用公开接口（限流）
            ss_papers = fetch_papers_by_keywords(keywords, year=2026, max_results=max_papers)
            for p in ss_papers:
                p["topic"] = topic_name
        
        # 3. 合并去重
        all_topic_papers = arxiv_papers + ss_papers
        seen_ids = set()
        unique_papers = []
        for p in all_topic_papers:
            pid = p.get("id", "")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                unique_papers.append(p)
        
        # 4. 排序
        ranked = rank_papers(
            unique_papers,
            time_decay_days=ranking_config.get("time_decay_days", 7),
            citation_weight=ranking_config.get("citation_weight", 0.6),
            recency_weight=ranking_config.get("recency_weight", 0.4),
            min_citations=ranking_config.get("min_citations", 0),
        )
        
        # 5. 截取Top N
        ranked = ranked[:max_papers]
        
        if verbose:
            print(f"   → 抓取 {len(all_topic_papers)} 篇，去重后 {len(unique_papers)} 篇，取Top {len(ranked)}")
        
        all_papers.extend(ranked)
    
    if not all_papers:
        print("[PaperRadar] 未抓取到任何论文，请检查关键词配置")
        return []
    
    # 6. 归档
    archived = archive_papers(all_papers, output_dir=output_dir)
    if verbose:
        print(f"\n✅ 归档完成: {len(archived)} 篇")
    
    # 7. 构建索引
    index_path = build_index(all_papers, output_path="./output/knowledge_base.json")
    if verbose:
        print(f"✅ 索引构建: {index_path}")
    
    # 8. 生成digest
    digest_path = generate_digest(all_papers, output_path=f"{digest_dir}/YYYY-MM-DD.md")
    if verbose:
        print(f"✅ Digest生成: {digest_path}")
    
    if verbose:
        simple = generate_simple_digest(all_papers)
        print("\n" + "=" * 50)
        print("今日摘要预览:")
        print("=" * 50)
        print(simple)
    
    return all_papers


def main():
    parser = argparse.ArgumentParser(description="PaperRadar - AI论文追踪与归档工具")
    parser.add_argument("--config", default="./config.yaml", help="配置文件路径")
    parser.add_argument("--topics", default="", help="指定追踪领域（逗号分隔，不指定则跑全部）")
    parser.add_argument("--days", type=int, default=7, help="抓取近N天论文 (默认7)")
    parser.add_argument("--ss-key", default="", help="Semantic Scholar API Key")
    parser.add_argument("--verbose", action="store_true", default=True)
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    topics = args.topics.split(",") if args.topics else None
    
    run_pipeline(
        config=config,
        topics=topics,
        days_back=args.days,
        api_key=args.ss_key or config.get("api_keys", {}).get("semantic_scholar", ""),
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
