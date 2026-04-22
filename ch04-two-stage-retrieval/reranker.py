"""
第四章：BGE-Reranker Cross-Encoder 精排
注意：使用 sentence-transformers 的 CrossEncoder，
不要用 FlagEmbedding.FlagReranker（与 transformers 5.x 不兼容）
"""
import os
from typing import List
from sentence_transformers import CrossEncoder
from milvus_client import Doc


class BGEReranker:
    def __init__(self):
        model_path = os.getenv("RERANKER_MODEL_PATH", "/data/bge-reranker")
        self.model = CrossEncoder(model_path, max_length=512)

    def rerank(self, query: str, documents: List[Doc]) -> List[Doc]:
        if not documents:
            return documents

        # 构造 [query, doc] 对，Cross-Encoder 一起编码（交叉注意力）
        pairs = [[query, doc.content] for doc in documents]

        # 打分，返回每对的相关性分数（0~1）
        scores = self.model.predict(pairs)

        for doc, score in zip(documents, scores):
            doc.rerank_score = float(score)

        # 按精排分数降序
        return sorted(documents, key=lambda x: x.rerank_score, reverse=True)
