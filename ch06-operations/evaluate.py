"""
第六章：黄金测试集自动评估脚本
每次知识库更新后运行，准确率 < 80% 则退出码为 1（可接入 CI）
"""
import json
import sys
import urllib.request
from pathlib import Path

KNOWLEDGE_API = "http://localhost:8000"
GOLDEN_SET_FILE = Path(__file__).parent / "golden_test_set.json"


def search(query: str, top_k: int = 5) -> list:
    payload = json.dumps({"query": query, "top_k": top_k}).encode()
    req = urllib.request.Request(
        f"{KNOWLEDGE_API}/api/knowledge/search",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["results"]


def evaluate(test_cases: list) -> dict:
    hits = 0
    failures = []

    for case in test_cases:
        query = case["query"]
        expected_keywords = case["expected_keywords"]

        try:
            results = search(query, top_k=5)
            top1_content = results[0]["content"] if results else ""
        except Exception as e:
            print(f"搜索异常: {query} - {e}")
            top1_content = ""

        # 关键词命中率
        hit_count = sum(1 for kw in expected_keywords if kw in top1_content)
        keyword_hit_rate = hit_count / len(expected_keywords)
        passed = keyword_hit_rate >= 0.7

        if passed:
            hits += 1
        else:
            failures.append({
                "query": query,
                "keyword_hit_rate": keyword_hit_rate,
                "top1_preview": top1_content[:80],
            })

    accuracy = hits / len(test_cases) if test_cases else 0
    return {"accuracy": accuracy, "failures": failures, "total": len(test_cases)}


def main():
    if not GOLDEN_SET_FILE.exists():
        print(f"⚠️  未找到黄金测试集: {GOLDEN_SET_FILE}")
        print("   请参考 golden_test_set.example.json 创建测试数据")
        sys.exit(0)

    test_cases = json.loads(GOLDEN_SET_FILE.read_text(encoding="utf-8"))
    result = evaluate(test_cases)

    print(f"\n=== 评估结果 ===")
    print(f"准确率: {result['accuracy']:.1%}  ({result['total'] - len(result['failures'])}/{result['total']})")

    if result["failures"]:
        print(f"\n❌ 失败的 case ({len(result['failures'])} 条):")
        for f in result["failures"]:
            print(f"  [{f['keyword_hit_rate']:.0%}] {f['query']}")
            print(f"        Top1: {f['top1_preview']}...")

    if result["accuracy"] < 0.80:
        print("\n⚠️  准确率低于 80%，请排查后再上线")
        sys.exit(1)
    else:
        print("\n✅ 评估通过")


if __name__ == "__main__":
    main()
