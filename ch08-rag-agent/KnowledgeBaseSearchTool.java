package cn.example.agent.tool;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;

/**
 * 第八章：知识库搜索 Tool
 * 调用 Python 知识库服务（两阶段检索），将结果注入 LLM 上下文
 */
@Component
public class KnowledgeBaseSearchTool implements AgentTool {

    @Value("${knowledge.api.url}")
    private String knowledgeApiUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    @Override
    public String getName() {
        return "knowledge_base_search";
    }

    @Override
    public String getDescription() {
        // 描述要告诉 LLM：什么时候调、查什么、不适合查什么
        return "搜索企业知识库，获取业务规则、操作流程、指标定义等知识性内容。" +
               "适用于：用户询问规则/流程/术语定义时。" +
               "不适用于：查询实时数据（销量/库存/价格）。" +
               "返回：最相关的 5 条知识片段，含标题和内容。";
    }

    @Override
    public Map<String, Object> getInputSchema() {
        return Map.of(
            "type", "object",
            "properties", Map.of(
                "query", Map.of(
                    "type", "string",
                    "description", "检索关键词或问题，支持中文自然语言"
                )
            ),
            "required", List.of("query")
        );
    }

    @Override
    @SuppressWarnings("unchecked")
    public Object execute(Map<String, Object> input) {
        String query = (String) input.get("query");
        Map<String, Object> request = Map.of("query", query, "top_k", 5);
        Map<String, Object> response = restTemplate.postForObject(
            knowledgeApiUrl + "/api/knowledge/search",
            request,
            Map.class
        );
        return response != null ? response.get("results") : List.of();
    }

    @Override
    public String getDisplayName() {
        return "搜索知识库";
    }
}
