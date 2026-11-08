# 客服智能体 MCP Server（mcp-server-csagent）

> 把智能客服 Agent 的 5 个业务工具改造为 MCP（Model Context Protocol）标准服务，
> 供任意 MCP Client（Claude Desktop / Cursor / 自研 Agent）调用。
> 简历表述：「熟悉 MCP 协议，实践过业务工具链的 MCP 化改造」。

## 快速开始

```bash
pip install "mcp<2"
python3 server.py          # stdio 模式，供 MCP Client 拉起
```

### Claude Desktop 接入（claude_desktop_config.json）

```json
{
  "mcpServers": {
    "csagent": {
      "command": "python3",
      "args": ["/绝对路径/server.py"]
    }
  }
}
```

### MCP Inspector 调试

```bash
npx @modelcontextprotocol/inspector python3 server.py
```

## 工具清单（与客服 Agent 场景一一对应）

| 工具 | 功能 | 原Agent角色 |
|---|---|---|
| `knowledge_search` | 知识库检索（关键词+分类过滤） | RAG 检索入口 |
| `create_ticket` | 创建工单（标题/描述/优先级） | 工单系统对接 |
| `query_order` | 订单查询（订单号/手机号） | 业务系统对接 |
| `query_logs` | 服务日志查询（时间窗+级别） | 运维排查 |
| `send_email` | 发送通知邮件 | 消息触达 |

## 与 ReAct Agent 的关系

原架构：`LLM → Function Calling → 5个工具函数`（工具与 Agent 强耦合）
MCP 化后：`LLM → MCP Client → MCP协议 → 本Server（工具独立进程）`

收益：
1. **工具解耦**：业务工具独立部署/版本管理，任何 MCP Client 都能复用
2. **协议标准化**：不再依赖特定 Agent 框架的工具注册方式
3. **权限边界清晰**：server 侧可独立鉴权与审计
