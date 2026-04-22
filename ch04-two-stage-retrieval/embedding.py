"""
第四章：BGE-Large 向量化封装
"""
import os
from typing import List
from sentence_transformers import SentenceTransformer


class BGEEmbedder:
    def __init__(self):
        # 路径从环境变量读取，禁止硬编码
        model_path = os.getenv("BGE_MODEL_PATH", "/data/bge-models")
        self.model = SentenceTransformer(model_path)

    def encode(self, texts: List[str]) -> List[List[float]]:
        # normalize_embeddings=True：COSINE相似度等价于点积，检索更快
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False
        ).tolist()

    def encode_one(self, text: str) -> List[float]:
        return self.encode([text])[0]
