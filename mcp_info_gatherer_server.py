"""MCP Info Gatherer — точка входа.

Запуск:
  uv run mcp-info-gatherer --transport stdio
  uv run mcp-info-gatherer --transport sse --host 127.0.0.1 --port 8003
"""

from mcp_info_gatherer.server import main

if __name__ == "__main__":
    main()
