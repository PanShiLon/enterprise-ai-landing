#!/bin/bash
# 第六章：服务健康检查脚本
# 用法：加入 crontab，每 5 分钟执行一次
#   */5 * * * * /opt/scripts/health_check.sh

DINGTALK_WEBHOOK="${DINGTALK_WEBHOOK:-}"  # 从环境变量读取，不硬编码

alert() {
    local msg="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $msg"
    if [ -n "$DINGTALK_WEBHOOK" ]; then
        curl -s -X POST "$DINGTALK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"$msg\"}}" > /dev/null
    fi
}

# 1. 检查 knowledge-service 容器
if ! docker ps --format '{{.Names}}' | grep -q "knowledge-service"; then
    alert "知识库服务(knowledge-service)宕机，请立即处理！"
fi

# 2. 检查 Milvus
if ! curl -sf http://localhost:9091/healthz | grep -q "OK"; then
    alert "Milvus 健康检查失败！"
fi

# 3. 检查搜索接口可用性
response=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST http://127.0.0.1:8000/api/knowledge/search \
    -H 'Content-Type: application/json' \
    -d '{"query":"测试","top_k":1}')

if [ "$response" != "200" ]; then
    alert "搜索接口异常，HTTP状态码: $response"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 健康检查完成"
