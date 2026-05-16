# AI Smart Search (智能深度搜索助手)

一个基于 MCP (Model Context Protocol) 的智能搜索工具，结合了 Tavily 网络搜索与小米 MiMo AI 深度分析能力。

## 功能

提供1个 MCP 工具：

### `deep_search(query, max_results=5, language="中文")`

1. 使用 Tavily Search API 进行网络搜索
2. 将搜索结果发送给小米 MiMo AI（mimo-v2.5-pro）进行深度分析和总结
3. 返回结构化结果：AI 分析总结 + 参考来源列表

## 安装

### 前置要求

- Python 3.10+
- 有效的 Tavily API Key
- 有效的小米 MiMo API Key

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export MIMO_API_KEY="your-mimo-api-key"
export TAVILY_API_KEY="your-tavily-api-key"

# 运行（stdio 模式）
python entry.py
```

### MCP 配置

在 MCP 客户端配置中添加：

```json
{
  "mcpServers": {
    "ai-smart-search": {
      "command": "python",
      "args": ["/path/to/entry.py"],
      "env": {
        "MIMO_API_KEY": "your-mimo-api-key",
        "TAVILY_API_KEY": "your-tavily-api-key"
      }
    }
  }
}
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MIMO_API_KEY` | 小米 MiMo API Key | - |
| `MIMO_BASE_URL` | MiMo API 基础 URL | https://token-plan-cn.xiaomimimo.com/v1 |
| `MIMO_MODEL` | MiMo 模型名称 | mimo-v2.5-pro |
| `TAVILY_API_KEY` | Tavily Search API Key | - |

## 技术栈

- Python 3.x
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Tavily Search API
- 小米 MiMo API (mimo-v2.5-pro)
- Stdio 传输协议

## 许可证

MIT
