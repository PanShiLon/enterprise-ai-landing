"""
第三章：Layer 3+4 标准化去重 + 入库质检
"""
from dataclasses import dataclass, field
from typing import List, Optional
import math


@dataclass
class Chunk:
    question: str
    answer: str
    keywords: List[str]
    source: str
    priority: str = "P2"          # P0/P1/P2/P3
    embedding: Optional[List[float]] = field(default=None, repr=False)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def deduplicate(chunks: List[Chunk]) -> List[Chunk]:
    """语义去重：相似度 > 0.85 的条目合并保留一条"""
    kept: List[Chunk] = []
    for chunk in chunks:
        # 长度校验
        if len(chunk.question) < 10 or len(chunk.answer) < 20:
            continue
        # 语义去重（需要 embedding 已填充）
        if chunk.embedding:
            duplicate = any(
                cosine_similarity(chunk.embedding, k.embedding) > 0.85
                for k in kept if k.embedding
            )
            if duplicate:
                continue
        kept.append(chunk)
    return kept


def detect_contradiction(chunk: Chunk) -> bool:
    """简单矛盾检测：问题和答案语义相似度过高（Q/A几乎一样）说明答案没有增量信息"""
    # 实际生产中可用 embedding 计算，这里用关键词重叠率简单估算
    q_words = set(chunk.question)
    a_words = set(chunk.answer)
    overlap = len(q_words & a_words) / max(len(q_words), 1)
    return overlap > 0.9


def quality_score(chunk: Chunk) -> float:
    """质检打分，≥ 0.7 自动入库，< 0.7 进人工审核队列"""
    score = 0.0
    score += 0.4 if len(chunk.answer) >= 50 else 0.2   # 完整性
    score += 0.3 if chunk.keywords else 0.0             # 关键词
    score += 0.3 if not detect_contradiction(chunk) else 0.0  # 无矛盾
    return score


def run_quality_check(chunks: List[Chunk]):
    """运行质检流水线，返回 (auto_pass, need_review)"""
    auto_pass = []
    need_review = []

    for chunk in chunks:
        score = quality_score(chunk)
        if score >= 0.7:
            auto_pass.append(chunk)
        else:
            need_review.append((chunk, score))

    print(f"✅ 自动通过: {len(auto_pass)} 条")
    print(f"👤 人工审核: {len(need_review)} 条")

    for chunk, score in need_review[:5]:
        print(f"   [{score:.1f}] Q: {chunk.question[:30]}...")

    return auto_pass, need_review
