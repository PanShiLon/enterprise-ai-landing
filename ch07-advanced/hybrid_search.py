"""
第七章：混合检索 - BM25 关键词召回 + RRF 融合
"""
from dataclasses import dataclass
from typing import List


@dataclass
class Doc:
    id: str
    content: str
    score: float = 0.0


class BM25Retriever:
    """
    内存 BM25 检索，适合知识库 < 10 万条的场景。
    超过 10 万条建议换 Elasticsearch。
    """

    def __init__(self, documents: List[Doc]):
        try:
            import jieba
            from rank_bm25 import BM25Okapi
        except ImportError:
            raise ImportError("pip install rank-bm25 jieba")

        self.documents = documents
        tokenized = [list(jieba.cut(doc.content)) for doc in documents]
        self.bm25 = BM25Okapi(tokenized)
        self._jieba = jieba

    def search(self, query: str, top_k: int = 20) -> List[Doc]:
        tokens = list(self._jieba.cut(query))
        scores = self.bm25.get_scores(tokens)
        top_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:top_k]
        return [self.documents[i] for i in top_indices]


def rrf_fusion(
    vector_results: List[Doc],
    bm25_results: List[Doc],
    k: int = 60,
) -> List[Doc]:
    """
    倒数排名融合（Reciprocal Rank Fusion）
    每个结果的最终分数 = Σ 1/(k + rank_i)
    k=60 是经验值，平衡高排名和低排名的权重
    """
    scores: dict[str, float] = {}

    for rank, doc in enumerate(vector_results, 1):
        scores[doc.id] = scores.get(doc.id, 0.0) + 1.0 / (k + rank)

    for rank, doc in enumerate(bm25_results, 1):
        scores[doc.id] = scores.get(doc.id, 0.0) + 1.0 / (k + rank)

    all_docs = {doc.id: doc for doc in vector_results + bm25_results}
    ranked_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    return [all_docs[doc_id] for doc_id in ranked_ids]
