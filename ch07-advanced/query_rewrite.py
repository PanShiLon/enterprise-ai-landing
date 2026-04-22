"""
第七章：查询改写 - 同义词扩展 + 意图分类前缀
"""
from typing import Optional

# 业务术语同义词词表（需要根据实际业务维护）
BUSINESS_SYNONYMS: dict[str, list[str]] = {
    "格效": ["格位利用率", "格位效率", "格子利用率"],
    "投柜": ["投放设备", "点位铺设", "设备入场"],
    "改价": ["价格调整", "修改售价", "价格变更"],
    "机器": ["设备", "售货机", "终端"],
    "补货": ["库存补充", "商品补充", "进货"],
}

INTENT_CATEGORIES: dict[str, list[str]] = {
    "操作咨询": ["怎么", "如何", "步骤", "流程", "操作"],
    "故障排查": ["不了", "报错", "失败", "无法", "问题", "故障", "异常"],
    "数据查询": ["多少", "数量", "统计", "查看", "查询"],
    "规则说明": ["是什么", "定义", "标准", "要求", "规则"],
}


def synonym_expand(query: str) -> str:
    """把 query 中的业务术语扩展为全形式，提高召回率"""
    expanded = query
    for term, synonyms in BUSINESS_SYNONYMS.items():
        if term in query:
            expanded += " " + " ".join(synonyms)
    return expanded


def classify_intent(query: str) -> str:
    for intent, keywords in INTENT_CATEGORIES.items():
        if any(kw in query for kw in keywords):
            return intent
    return "通用"


def rewrite_query(query: str) -> str:
    """
    完整查询改写流程：
    1. 同义词扩展
    2. 意图分类前缀
    """
    expanded = synonym_expand(query)
    intent = classify_intent(query)
    return f"[{intent}] {expanded}"
