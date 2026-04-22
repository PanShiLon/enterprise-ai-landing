package cn.example.agent.service;

import cn.example.agent.tool.AgentTool;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.util.*;

/**
 * 第八章：ReAct Agent 核心服务
 * 实现 Reasoning + Acting 循环，支持多轮 Tool 调用
 */
@Service
public class AgentService {

    private final List<AgentTool> toolList;
    private Map<String, AgentTool> toolMap;

    private static final int MAX_ROUNDS = 10; // 防止死循环

    public AgentService(List<AgentTool> toolList) {
        this.toolList = toolList;
    }

    @PostConstruct
    public void init() {
        toolMap = new HashMap<>();
        for (AgentTool tool : toolList) {
            toolMap.put(tool.getName(), tool);
        }
    }

    public String chat(String sessionId, String userMessage) {
        List<Map<String, Object>> messages = loadHistory(sessionId);
        messages.add(buildUserMessage(userMessage));

        // ReAct 循环
        for (int round = 0; round < MAX_ROUNDS; round++) {
            // 截断消息历史，防止超出上下文窗口
            List<Map<String, Object>> truncated = truncateHistory(messages);

            // 调用 LLM
            Map<String, Object> response = callLLM(truncated);

            List<Map<String, Object>> toolCalls = getToolCalls(response);
            if (toolCalls != null && !toolCalls.isEmpty()) {
                // 把 LLM 的思考（含 tool_calls）加入历史
                // 注意：有 tool_calls 时不能带 content 字段（Kimi API 要求）
                messages.add(buildAssistantMessageWithTools(toolCalls));

                // 执行每个 Tool
                for (Map<String, Object> toolCall : toolCalls) {
                    String toolName = getToolName(toolCall);
                    Map<String, Object> args = getToolArgs(toolCall);
                    Object result = executeTool(toolName, args);
                    messages.add(buildToolResultMessage(getToolCallId(toolCall), result));
                }
            } else {
                // LLM 认为信息足够，生成最终回答
                String content = getContent(response);
                saveHistory(sessionId, messages);
                return content;
            }
        }

        return "处理超时，请简化您的问题后重试。";
    }

    private Object executeTool(String toolName, Map<String, Object> args) {
        AgentTool tool = toolMap.get(toolName);
        if (tool == null) {
            return "Tool 未找到：" + toolName;
        }
        try {
            Object result = tool.execute(args);
            return compressToolResult(result);
        } catch (Exception e) {
            return "执行失败：" + e.getMessage();
        }
    }

    /** Tool 结果压缩，防止撑爆 context */
    private Object compressToolResult(Object result) {
        if (result instanceof List) {
            List<?> list = (List<?>) result;
            if (list.size() > 20) {
                return list.subList(0, 20).toString()
                    + "\n（共 " + list.size() + " 条，已截取前 20 条）";
            }
        }
        String json = result.toString();
        if (json.length() > 4000) {
            return json.substring(0, 4000) + "...（已截断）";
        }
        return result;
    }

    /** 三步消息历史截断 */
    private List<Map<String, Object>> truncateHistory(List<Map<String, Object>> messages) {
        List<Map<String, Object>> result = new ArrayList<>(messages);

        // Step 1: 数量截断，保留最新 30 条
        if (result.size() > 30) {
            result = result.subList(result.size() - 30, result.size());
        }

        // Step 2: 长度截断（简化版）
        // Step 3: 修复孤立 tool 消息（略，完整实现见项目源码）
        return result;
    }

    // ---- 以下方法需根据实际 LLM SDK 实现 ----

    private Map<String, Object> callLLM(List<Map<String, Object>> messages) {
        // 调用 ModelGateway（Kimi 主 + DeepSeek 备）
        throw new UnsupportedOperationException("需接入实际 LLM SDK");
    }

    private List<Map<String, Object>> loadHistory(String sessionId) {
        return new ArrayList<>(); // 实际从 Redis/DB 加载
    }

    private void saveHistory(String sessionId, List<Map<String, Object>> messages) {
        // 实际保存到 Redis/DB
    }

    private Map<String, Object> buildUserMessage(String content) {
        return Map.of("role", "user", "content", content);
    }

    private Map<String, Object> buildAssistantMessageWithTools(
            List<Map<String, Object>> toolCalls) {
        // 有 tool_calls 时不能带 content 字段！（Kimi API 400 的根源）
        Map<String, Object> msg = new LinkedHashMap<>();
        msg.put("role", "assistant");
        msg.put("tool_calls", toolCalls);
        return msg;
    }

    private Map<String, Object> buildToolResultMessage(String toolCallId, Object result) {
        return Map.of(
            "role", "tool",
            "tool_call_id", toolCallId,
            "content", result.toString()
        );
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> getToolCalls(Map<String, Object> response) {
        return (List<Map<String, Object>>) response.get("tool_calls");
    }

    private String getContent(Map<String, Object> response) {
        return (String) response.getOrDefault("content", "");
    }

    private String getToolName(Map<String, Object> toolCall) {
        Map<?, ?> func = (Map<?, ?>) toolCall.get("function");
        return (String) func.get("name");
    }

    private String getToolCallId(Map<String, Object> toolCall) {
        return (String) toolCall.get("id");
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> getToolArgs(Map<String, Object> toolCall) {
        Map<?, ?> func = (Map<?, ?>) toolCall.get("function");
        String argsJson = (String) func.get("arguments");
        // 实际用 Jackson/Gson 解析
        return new HashMap<>();
    }
}
