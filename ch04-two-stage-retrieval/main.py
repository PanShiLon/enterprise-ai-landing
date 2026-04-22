"""
第四章：两阶段检索 FastAPI 服务入口
"""
import asyncio
import time
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from embedding import BGEEmbedder
from milvus_client import MilvusClient, Doc
from reranker import BGEReranker

# 并发控制：Cross-Encoder 是 CPU 密集型，限制最多 8 个并发推理
inference_semaphore = asyncio.Semaphore(8)

embedder: BGEEmbedder
milvus: MilvusClient
reranker: BGEReranker


@asynccontextmanager
async def lifespan(app: FastAPI):
    global embedder, milvus, reranker
    print("加载模型...")
    embedder = BGEEmbedder()
    milvus = MilvusClient()
    reranker = BGEReranker()
    print("模型加载完成")
    yield


app = FastAPI(lifespan=lifespan)


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResultItem(BaseModel):
    id: str
    title: str
    content: str
    category: str
    score: float
    rerank_score: Optional[float] = None  # 必须显式声明，否则被 FastAPI 静默过滤


class SearchResponse(BaseModel):
    results: List[SearchResultItem]
    latency_ms: float


@app.post("/api/knowledge/search", response_model=SearchResponse)
async def search_knowledge(request: SearchRequest):
    start = time.time()

    # 第一阶段：向量召回 Top20
    query_vector = embedder.encode_one(request.query)
    candidates = milvus.search(query_vector, top_k=20)

    # 第二阶段：Cross-Encoder 精排（并发控制）
    async with inference_semaphore:
        reranked = reranker.rerank(request.query, candidates)

    final = reranked[:request.top_k]
    latency_ms = (time.time() - start) * 1000

    return SearchResponse(
        results=[
            SearchResultItem(
                id=doc.id,
                title=doc.title,
                content=doc.content,
                category=doc.category,
                score=doc.score,
                rerank_score=doc.rerank_score,
            )
            for doc in final
        ],
        latency_ms=round(latency_ms, 1),
    )


@app.get("/health")
def health():
    return {"status": "ok"}
