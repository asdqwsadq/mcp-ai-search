"""
AI Smart Search - MCP Tool
智能深度搜索助手
Combines Tavily search with Xiaomi MiMo AI analysis.
"""

import json
import os
import sys
from typing import Any

import httpx
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, TextContent, Tool


# ── Configuration ──────────────────────────────────────────────────────────

MIMO_API_KEY = os.environ.get(
    "MIMO_API_KEY",
    "tp-c6w5jsmi9x28pgwhuq8gh9bshuib12qx7f3brwc80orthn51",
)
MIMO_BASE_URL = os.environ.get(
    "MIMO_BASE_URL",
    "https://token-plan-cn.xiaomimimo.com/v1",
)
MIMO_MODEL = os.environ.get("MIMO_MODEL", "mimo-v2.5-pro")

TAVILY_API_KEY = os.environ.get(
    "TAVILY_API_KEY",
    "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",
)

# ── Tavily Search ──────────────────────────────────────────────────────────


async def tavily_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Search the web using Tavily Search API."""
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": max_results,
        "search_depth": "advanced",
        "include_answer": False,
        "include_raw_content": False,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError:
            print(f"⚠️ Tavily API error {resp.status_code}: {resp.text[:300]}", file=sys.stderr)
            return []
        data = resp.json()
        results = data.get("results", [])
        cleaned = []
        for r in results:
            cleaned.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
            })
        return cleaned


# ── MiMo AI Analysis ──────────────────────────────────────────────────────


async def mimo_analyze(
    query: str,
    search_results: list[dict[str, Any]],
    language: str = "中文",
) -> str:
    """Send search results to MiMo for deep analysis and summary."""
    results_text = []
    for i, r in enumerate(search_results, 1):
        results_text.append(
            f"[{i}] {r['title']}\n   URL: {r['url']}\n   摘要: {r['content'][:800]}"
        )
    context = "\n\n".join(results_text)

    system_prompt = f"""你是一个专业的智能搜索分析助手。你的任务是基于搜索到的网络信息，对用户的问题进行深度分析。

请使用{language}回答。

分析要求：
1. 先对查询主题进行简要概述
2. 从搜索结果中提取关键信息，按重要程度组织
3. 对信息进行交叉验证，指出可能存在的矛盾或不确定性
4. 给出综合性的结论或建议
5. 如果信息不足，明确说明局限性

最后请附上参考来源的链接列表。"""

    user_prompt = f"""用户查询：{query}

搜索结果如下：

{context}

请基于以上搜索结果进行深度分析和总结。"""

    headers = {
        "Authorization": f"Bearer {MIMO_API_KEY}",
        "api-key": MIMO_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "model": MIMO_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 4096,
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(
            f"{MIMO_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
        )
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError:
            print(f"⚠️ MiMo API error {resp.status_code}: {resp.text[:500]}", file=sys.stderr)
            return f"小米 MiMo API 返回错误 (HTTP {resp.status_code})，请稍后重试。"
        data = resp.json()
        return data["choices"][0]["message"]["content"]


# ── MCP Server ─────────────────────────────────────────────────────────────

server = Server("ai-smart-search")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="deep_search",
            description="智能深度搜索：先通过网络搜索获取信息，再利用 AI 进行深度分析和总结",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询内容",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大搜索结果数量（1-10）",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10,
                    },
                    "language": {
                        "type": "string",
                        "description": "分析和回答使用的语言（默认：中文）",
                        "default": "中文",
                    },
                },
                "required": ["query"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    if name != "deep_search":
        raise ValueError(f"Unknown tool: {name}")

    query = arguments["query"]
    max_results = arguments.get("max_results", 5)
    language = arguments.get("language", "中文")

    # Step 1: Tavily search
    print(f"🔍 正在搜索: {query}", file=sys.stderr)
    search_results = await tavily_search(query, max_results)

    if not search_results:
        return CallToolResult(
            content=[TextContent(type="text", text="没有找到搜索结果。")]
        )

    # Step 2: MiMo analysis
    print(f"🧠 正在调用小米 MiMo 进行深度分析...", file=sys.stderr)
    analysis = await mimo_analyze(query, search_results, language)

    # Build output
    sources = []
    for r in search_results:
        sources.append({"title": r["title"], "url": r["url"]})

    output = {
        "query": query,
        "analysis": analysis,
        "sources": sources,
        "total_sources": len(sources),
    }

    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(output, ensure_ascii=False, indent=2))]
    )


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
