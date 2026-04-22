"""
第四章：Milvus 向量库客户端
"""
import os
from dataclasses import dataclass
from typing import List, Optional
from pymilvus import Collection, connections, FieldSchema, CollectionSchema, DataType, utility


COLLECTION_NAME = "knowledge_base"
VECTOR_DIM = 1024  # BGE-Large-zh-v1.5 维度


@dataclass
class Doc:
    id: str
    title: str
    content: str
    category: str
    score: float = 0.0
    rerank_score: Optional[float] = None


class MilvusClient:
    def __init__(self):
        host = os.getenv("MILVUS_HOST", "localhost")
        port = os.getenv("MILVUS_PORT", "19530")
        connections.connect(host=host, port=port)
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self) -> Collection:
        if utility.has_collection(COLLECTION_NAME):
            col = Collection(COLLECTION_NAME)
            col.load()
            return col

        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR,
                        max_length=64, is_primary=True),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=4096),
            FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR,
                        dim=VECTOR_DIM),
        ]
        schema = CollectionSchema(fields)
        col = Collection(COLLECTION_NAME, schema)

        col.create_index(
            field_name="embedding",
            index_params={
                "metric_type": "COSINE",   # 建库/建索引/搜索必须一致
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024},
            }
        )
        col.load()
        return col

    def search(self, query_vector: List[float], top_k: int = 20) -> List[Doc]:
        results = self.collection.search(
            data=[query_vector],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"nprobe": 10}},
            limit=top_k,
            output_fields=["id", "title", "content", "category"]
        )
        docs = []
        for hit in results[0]:
            docs.append(Doc(
                id=hit.entity.get("id"),
                title=hit.entity.get("title"),
                content=hit.entity.get("content"),
                category=hit.entity.get("category"),
                score=hit.score,
            ))
        return docs

    def upsert(self, doc_id: str, title: str, content: str,
               category: str, embedding: List[float]):
        # 先删除旧记录（如存在）
        self.collection.delete(expr=f'id == "{doc_id}"')
        self.collection.insert([
            [doc_id], [title], [content], [category], [embedding]
        ])
        self.collection.flush()
