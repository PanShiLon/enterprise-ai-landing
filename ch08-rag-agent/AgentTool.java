package cn.example.agent.tool;

import java.util.Map;

/**
 * 第八章：Agent Tool 统一接口
 * 所有 Tool 实现此接口，Spring 自动装配后由 AgentService 统一调用
 */
public interface AgentTool {

    /** Tool 名称，snake_case，LLM 按此名称调用 */
    String getName();

    /**
     * Tool 描述 —— 这是最重要的字段！
     * LLM 靠这个决定"何时调用、传什么参数"
     * 格式：适用场景 + 输入说明 + 返回说明
     */
    String getDescription();

    /** 参数 JSON Schema，告诉 LLM 参数结构 */
    Map<String, Object> getInputSchema();

    /** 执行 Tool，返回结果（会被 ToolResultCompressor 压缩后加入消息历史） */
    Object execute(Map<String, Object> input);

    /** SSE 状态展示名，展示给前端用 */
    default String getDisplayName() {
        return getName();
    }

    /** 是否写操作，true 时需要权限校验 */
    default boolean isWriteOperation() {
        return false;
    }
}
